#pragma once

#include <string>
#include <sstream>
#include <QObject>
#include <QApplication>
#include "../request.h"
#include "../qwidget-json-helpers.h"
#include "../qobject-utils.h"

namespace qnject {

    // TODO: move these and PODs out to a separate http-handlers/types.h
    using String = std::string;
    using Json = nlohmann::json;

    using qnject::helpers::address_to_string;

    // Misc QT helpers ----------------- --------------------------------------------

    // move to : vaccine/utils/qobject-finders.h
    // namespace {

    // Helper to invoke a function on a qobject if it has the specified name
    template<typename Functor>
    inline void with_object(const char* objectName, int& statusCode, Functor fn) {
        statusCode = 404;

        for (QWidget* child : qApp->allWidgets()) {
            if (child && (child->objectName() == objectName ||
                          objectName == std::to_string((uintptr_t) child))) {
                statusCode = 200;
                fn(child);
            }
        }
    }


}


namespace brilliant {
    //
    // move to : vaccine/request/response.h
    // ------------------------------------

    // Abstract response:
    // a response is any type that can write itselt into an mg_connection

    // TODO: move these and PODs out to a separate http-handlers/types.h

    struct response_prototype_t {
        // the only requirement for a response object is to have an
        // operator()() method taking the connection and writes it to
        // the response
        bool operator()(mg_connection* conn);
    };


    namespace response {

        using String = std::string;

        struct data_response_t {

            const int statusCode;
            const std::vector<char> data;
            const std::string headers;

            bool operator()(mg_connection* conn) const {

                const int dataSizeAsInt = (int) data.size();
                DLOG_F(INFO, "Sending %d bytes", dataSizeAsInt);

                mg_send_head(conn, 200, dataSizeAsInt, headers.c_str());
                mg_send(conn, data.data(), dataSizeAsInt);

                // why one would send fe. an image as 404 is beyond me
                return (statusCode >= 200 && statusCode <= 299);

            }

        };


        String headersForContentType(const String& contentType) {
            static const String headers =
                    "Access-Control-Allow-Origin: *\r\n"
                            "Access-Control-Allow-Headers: Origin, X-Requested-With, Content-Type, Accept\r\n"
                            "Content-Type: ";
            return headers + contentType;
        }


        template<typename InputIterator>
        data_response_t fromData(int statusCode, String contentType, InputIterator start, InputIterator end) {
            return {statusCode, std::vector<char>(start, end), headersForContentType(contentType)};
        }


        // Returns a new response from the given memory
        data_response_t fromMemoryBlock(int statusCode, String contentType, const void* start, size_t size) {
            const char* p = (const char*) start;
            return {statusCode, std::vector<char>(p, p + size), headersForContentType(contentType)};
        }

        template<typename Container>
        data_response_t fromContainer(int statusCode, String contentType, Container&& c) {
            using std::begin;
            using std::end;
            return fromData(statusCode, contentType, begin(c), end(c));
        }


        // ---------------------------------


        data_response_t error(int statusCode, String message) {
            return fromContainer(statusCode, "text/plain", message);
        }


        // Tries to run fn(args...) and log any errors
        template<typename Fn, typename... Args>
        data_response_t wrapErrors(Fn fn, Args&& ...args) {
            try {
                return fn(args...);
            } catch (std::exception& ex) {
                DLOG_F(ERROR, "Exception: %s", ex.what());
                return error(500, "Exception occured");
            }
        }

    }
}

namespace qnject {

    using brilliant::response::data_response_t;

    data_response_t json_response(int statusCode, Json data) {
        return brilliant::response::fromContainer(statusCode, "application/json", data.dump(2));
    }


}



// GENERIC HANDLERS
//
namespace qnject {
    namespace api {


        // send json response to the client
        inline void send_json(struct mg_connection* nc, nlohmann::json& j, int statusCode) {
            static const auto headers =
                    "Access-Control-Allow-Origin: *\r\n"
                            "Access-Control-Allow-Headers: Origin, X-Requested-With, Content-Type, Accept\r\n"
                            "Content-Type: application/json";

            std::string d = j.dump(2);

            mg_send_head(nc, statusCode, d.length(), headers);
            mg_send(nc, d.c_str(), d.length());
        }

        // using namespace brilliant::route;

        // for now use these, revisit later
        using Request = brilliant::Request;

        // GENERIC JSON HANDLER --------------------------
        //

        template<typename Handler>
        struct json_handler_t {
            Handler fn;

            template<typename ...Args>
            bool operator()(const Request& r, Args ...args) const {
                // lvalue is needed here
                Json ret = fn(r, args...);
                send_json(r.connection, ret, 200);
                return true;
            }
        };

        template<typename Handler>
        json_handler_t<Handler> wrap_json(Handler h) {
            return {h};
        }


        // GENERIC QOBJECT HANDLER --------------------------
        //
        // Maps a single URL parameter to a list of QObjects with the name,
        // maps Handler on them and returns the concatenated response as JSON.


        // Wraps a QObject -> Json request
        template<typename Handler>
        struct qobject_handler_t {
            Handler fn;

            bool operator()(const Request& r, String object_name) const {
                // take a single URL parameter
                int statusCode = 200;
                Json resp;

                DLOG_F(INFO, "Requesting data for QObject by name ='%s'", object_name.c_str());
                with_object(object_name.c_str(), statusCode, [&](QObject* obj) {
                    auto addr = address_to_string(obj);
                    DLOG_F(INFO, "Object found @ %s : name ='%s'", addr.c_str(), object_name.c_str());
                    resp.push_back({addr, fn(r, obj)});
                });

                // if error
                if (statusCode < 299) {
                    send_json(r.connection, resp, statusCode);
                    return true;
                }

                // we didn't find widget like this
                Json err = {{"error", "Widget not found"}};
                send_json(r.connection, err, statusCode);
                return false;
            }
        };


        // ----------------------------------------
        // Wraps a handler, we need to auto here to keep our sanity.
        template<typename Fn>
        decltype(auto) qobject_handler(Fn fn) {
            using namespace brilliant::route;
            return handler("object-name", qobject_handler_t<Fn>{fn});
        };


        // QOBJECT BY POINTER HANDLER BASE ---------------------------

        // Maps a single URL parameter to a single QObject with the url parameter as address,
        // maps Handler on them and returns the response as JSON.

        // ----------------------------------------
        // Helper to invoke a function on a qobject if it has the specified name
        struct with_object_at_address_safe_t {
            template<typename Functor>
            data_response_t operator()(const String& addrStr, Functor fn) const {
                using namespace brilliant;
                auto addr = (uintptr_t)helpers::stringToAddress(addrStr);


                for (QWidget* child : qApp->allWidgets()) {
                    auto childAddr = (uintptr_t)child;
                    if (child != nullptr && (addr == childAddr)) {
                        return fn(child);
                    }
                }

                return response::error(404, String("Cannot find object @ ") + addrStr);
            }
            static const with_object_at_address_safe_t instance;
        };


        // ----------------------------------------
        // Unsafe version: tries to create a pointer out of a memory address.
        //
        // DANGER! DANGER! DANGER! ========================================
        //
        // THIS WILL SEGFAULT THE APPLICATION IF THE MEMORY ADDRESSS ISNT VALID.
        //
        struct with_object_at_address_unsafe_t {
            template<typename Functor>
            data_response_t operator()(const String& addrStr, Functor fn) const {
                using namespace brilliant;


                void* addr = helpers::stringToAddress(addrStr);

                if (addr == nullptr) {
                    return response::error(404, "Cannot find object at invalid address");
                }


                // HERE WE GO. DANGER. DANGER. DANGER.
                QObject* obj = (QObject*)addr;
                if (qobject_cast<QObject*>(obj) == nullptr) {
                    return response::error(404, "Cannot cast object at address to QObject");
                }

                return fn(obj);
            }
        };


        // ----------------------------------------
        // Wraps a QObject -> Json request
        template<typename Getter, typename Handler>
        struct qobject_by_address_handler_t {
            Getter getter;
            Handler fn;

            bool operator()(const Request& r, String object_address) const {

                DLOG_F(INFO, "Requesting object @ '%s'", object_address.c_str());
                auto response = getter(object_address, [&](QObject* obj) {
                    auto addr = address_to_string(obj);
                    return fn(r, obj);
                });

                return response(r.connection);
            }
        };


        template<typename Getter, typename Handler>
        qobject_by_address_handler_t<Getter, Handler> make_qobject_address_handler(Getter g, Handler h) {
            return { g, h };
        }


        // ----------------------------------------
        // Base handler wrapper for objectAtAddress.
        // This allows to customize the resolver function.
        template<typename Fn, typename Getter>
        decltype(auto) qobject_at_address_handler_base(Getter g, Fn fn) {
            return brilliant::route::handler("0xaddress", make_qobject_address_handler(g,fn));
        };

        // Safe version of getting a widget by address.
        // This only gets the QWidgets that are in the QApplications allWidgets list.
        // (So QActions etc. need to be handled differently)
        template<typename Fn>
        decltype(auto) qobject_at_address_handler(Fn fn) {
			return brilliant::route::handler("0xaddress", make_qobject_address_handler(with_object_at_address_safe_t{}, fn));
//            return qobject_at_address_handler_base(with_object_at_address, fn);
        };


        // UnSafe version of getting a widget by address.
        // This only gets the QWidgets that are in the QApplications allWidgets list.
        // (So QActions etc. need to be handled differently)
        template<typename Fn>
        decltype(auto) qobject_at_address_handler_unsafe(Fn fn) {
            return qobject_at_address_handler_base(with_object_at_address_unsafe_t{}, fn);
        };



        // WRAP FUNCTIONS RETURNING JSON ----------------------------------------

        // Wraps a handler that returns a Json object into a handler that returns
        // a data_response_t

        template<typename Fn>
        struct json_wrapped_result_t {
            Fn fn;

            template<typename... Args>
            data_response_t operator()(Args...args) const {
                using brilliant::response::wrapErrors;
                return wrapErrors([&]() { return json_response(200, fn(args...)); });
            }
        };

        template<typename Fn>
        json_wrapped_result_t<Fn> json_wrapped_result(Fn fn) {
            return { fn };
        }

        // Wraps a handler
        template<typename Fn>
        decltype(auto) qobject_at_address_json_handler(Fn fn) {
            return qobject_at_address_handler(json_wrapped_result_t<Fn>{fn});
        };




        // NOT FOUND :) -----------------------------------------------------
        //
        bool method_not_found(const Request& r) {
            String uri = r.req["uri"];
            DLOG_F(WARNING, "Unhandled request: %s", uri.c_str());

            Json resp;
            resp["error"] = "Method not found";
            send_json(r.connection, resp, 404);
            return true;
        }


    }
}
