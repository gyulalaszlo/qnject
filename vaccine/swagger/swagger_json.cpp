#include "swagger_json.h"

namespace {

    nlohmann::json s_swagger_json =
            nlohmann::json({
                                   {"swagger", "2.0"},
                                   {"info",    {
                                                       {"version", "0.1.0"},
                                                       {"title", "qnject - injected in-process HTTP server"}
                                               }
                                   },
                                   {"basePath", VACCINE_API_PREFIX},
                                   {"paths",   nlohmann::json({})}
                           });


}

namespace qnject {

    // return with swagger_json file
    nlohmann::json& swagger_json() { return s_swagger_json; };
}