# Genereate the swagger test executable

add_executable(qnject_swagger_json swagger_json_test.cpp swagger_json.cpp swagger_json.h)
target_link_libraries(qnject_swagger_json qnject)
