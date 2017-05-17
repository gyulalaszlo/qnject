#pragma once

#include "qnject_config.h"
#include "json.hpp"

#define VACCINE_API_PREFIX "/api"
#define VACCINE_SWAGGER_JSON "/swagger.json"

namespace qnject {

    const std::string PREFIX_VACCINE_API(VACCINE_API_PREFIX);
    const std::string PREFIX_VACCINE_SWAGGER_JSON(VACCINE_SWAGGER_JSON);

    ////////////////////////////////////////////////////////////////////////////
    // Get a reference to the swagger json file.
    nlohmann::json& swagger_json();
}
