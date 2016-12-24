#include "../config.h"
#include <stdio.h>
#include <string>
#include <map>

#include "../deps/mongoose/mongoose.h"
#include "../deps/json/json.hpp"

#include "vaccine.h"

namespace vaccine {

  // when it's true, we shut down the party :(
  bool shutdown = false;

  static const char *s_default_http_port = "8000";
  static struct mg_serve_http_opts s_http_server_opts;

  static std::map<std::string, t_vaccine_api_handler> s_uri_handlers;

  void register_callback(std::string handler, t_vaccine_api_handler function) {
    s_uri_handlers[handler] = function;
  }

  static int has_prefix(const struct mg_str *uri, const struct mg_str *prefix) {
    return uri->len > prefix->len && memcmp(uri->p, prefix->p, prefix->len) == 0;
  }

  std::string get_until_char(std::string const& s, char c)
  {
    std::string::size_type pos = s.find(c);
    if (pos != std::string::npos)
    {
      return s.substr(0, pos);
    }
    else
    {
      return s;
    }
  }

  void parse_request_body(struct http_message *hm, nlohmann::json & req)
  {
    if ( hm->body.len > 0 ) {
      std::string s;
      s.assign(hm->body.p, hm->body.len);
      try {
        req = nlohmann::json::parse(s);
      } catch (std::exception & ex ) {
        printf("Request body: %s\n", ex.what());
      }
    }
  }


  void send_json(struct mg_connection *nc, nlohmann::json & j, int statusCode) {
    std::string d = j.dump(2);

    mg_send_head(nc, statusCode, d.length(), "Content-Type: application/json");
    mg_send(nc,d.c_str(),d.length());
  }

  static void ev_handler(struct mg_connection *nc, int ev, void *ev_data) {
    struct http_message *hm = (struct http_message *) ev_data;
    static const struct mg_str api_prefix = MG_MK_STR("/api/");



    switch (ev) {
      case MG_EV_HTTP_REQUEST:
        if (has_prefix(&hm->uri, &api_prefix) && hm->uri.len - api_prefix.len > 0) {
          // API request
          std::string uri,handler;

          uri.assign(hm->uri.p + api_prefix.len, hm->uri.len - api_prefix.len);
          handler = get_until_char(uri,'/');
         
          // call registred handler
          printf("Request is %s\n", uri.c_str() );

          if ( s_uri_handlers.count(handler) == 1 ) {
            try {
              (*s_uri_handlers[handler])(uri,nc,ev_data,hm);
            } catch (std::exception & ex) {
              mg_http_send_error(nc, 500, ex.what() );
            } catch (...) {
              mg_http_send_error(nc, 500, "Unknwown error (exception)" );
            }
          }
          else 
            mg_http_send_error(nc, 404, "Handler not registred");
        } else {
          // static web shit
          mg_serve_http(nc, hm, s_http_server_opts); 
        }
        break;
      default:
        break;
    }
  }


  void start_thread() {
    struct mg_mgr mgr;
    struct mg_connection *nc;
    int i;
    const char * http_port = getenv("VACCINE_HTTP_PORT") == NULL ? s_default_http_port : getenv("VACCINE_HTTP_PORT");

    printf("Opening web server socket\n");

    /* Open listening socket */
    mg_mgr_init(&mgr, NULL);
    nc = mg_bind(&mgr, http_port, ev_handler);
    mg_set_protocol_http_websocket(nc);
    s_http_server_opts.document_root = "/tmp/a";

    /* Run event loop until signal is received */
    printf("Starting RESTful server on port %s\n", http_port);
    while (! shutdown) {
      mg_mgr_poll(&mgr, 1000);
    }

    /* Cleanup */
    mg_mgr_free(&mgr);

    printf("Exiting on shutdown request");
  }

}
