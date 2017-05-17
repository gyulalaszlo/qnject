#pragma once

#include "qnject_config.h"
#include "json.hpp"

#define VACCINE_API_PREFIX "/api"
#define VACCINE_SWAGGER_JSON "/swagger.json"

namespace qnject {

    const std::string PREFIX_VACCINE_API(VACCINE_API_PREFIX);
    const std::string PREFIX_VACCINE_SWAGGER_JSON(VACCINE_SWAGGER_JSON);

    ////////////////////////////////////////////////////////////////////////////
    // Helpers for serving the Swagger JSON
    namespace {
        // swagger service description
        static nlohmann::json s_swagger_json =
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

        // return with swagger_json file
        inline const nlohmann::json swagger_json() { return s_swagger_json; }
    }
}
