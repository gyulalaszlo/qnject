#pragma once

#include <string>
#include <chrono>
#include <functional>

#include "../deps/mongoose/mongoose.h"
#include "../deps/json/json.hpp"

namespace vaccine {

  // vaccine's state
  enum mg_state {
    UNINITALIZED = 0,
    INITALIZING = 1,
    RUNNING = 2,
    SHUTDOWN_REQUESTED = 3,
    NOT_RUNNING = 4
  };
  
  // state of the injection. RUNNING means it accepts HTTP connections
  extern mg_state state;

  // vaccine's start thread function
  extern void start_thread(); 

  // callback type for registering 
  typedef std::function<void(
      std::string & uri, 
      struct mg_connection *nc, 
      void *ev_data,
      struct http_message *hm)> t_vaccine_api_handler;

  // registers a handler (plug-in). it associates the handler URL with 
  // a function a callback. optionally, it allows to specift a swagger 
  // JSON definition for the REST API endpoints
  void register_callback(std::string handler, t_vaccine_api_handler function, 
      const unsigned char * swagger_spec = NULL); 
  
  // returns map of registred handlers
  const std::map<std::string, t_vaccine_api_handler> registered_handlers(); 

  // parsed contents of the swagger.json file
  const nlohmann::json swagger_json();


  // helper function to return with json response from handlers 
  void send_json(struct mg_connection *nc, nlohmann::json & j, int statusCode = 200);

  // waits until vaccine is up and runnig. optional timeout in ms, -1 infinity
  void wait_until_vaccine_is_running(std::chrono::microseconds usecs = std::chrono::microseconds(0));

  // The wait time for inifinite waits
  constexpr auto inifiniteWaitTime = std::chrono::hours(9999);
};

