#ifdef _MSC_VER
#include <process.h>
#endif

#include <thread>
#include "../../deps/loguru/loguru.hpp"

#include "../vaccine.h"



namespace {



#ifdef _MSC_VER

#define INVALID_THREAD_HANDLE 0x1337

    HANDLE hThread = (void*)INVALID_THREAD_HANDLE;


    unsigned __stdcall SecondThreadFunc(void* pArguments)
    {
        vaccine::start_thread();
        return 0;
    }

    struct dyld_insert_t_win {


        dyld_insert_t_win() {
			if (uintptr_t(hThread) == INVALID_THREAD_HANDLE) {
                printf("Staring service thread\n");
                vaccine::state = vaccine::mg_state::INITALIZING;
                unsigned threadID;
                if (uintptr_t(hThread) == INVALID_THREAD_HANDLE) {
                    hThread = (HANDLE)_beginthreadex(NULL, 0, &SecondThreadFunc, NULL, 0, &threadID);
                }
                printf("Started service thread\n");

            }
        }
        ~dyld_insert_t_win() {
			if (uintptr_t(hThread) != INVALID_THREAD_HANDLE) {
                DLOG_F(INFO, "Stopping service thread()");
                vaccine::state = vaccine::mg_state::SHUTDOWN_REQUESTED;
                //service_thread->join();
            }
        }


    };

    // boot
    dyld_insert_t_win onSpawn;
#else

    // *NIX allows us to use ((constructor))

    std::thread* service_thread = nullptr;

    // Initializer.
    __attribute__((constructor))
    static void initializer(void) {
        printf("Staring service thread\n");
        vaccine::state = vaccine::mg_state::INITALIZING;
        service_thread = new std::thread(vaccine::start_thread);
        printf("Started service thread\n");
    }

    // Finalizer.
    __attribute__((destructor))
    static void finalizer(void) {
        DLOG_F(INFO, "Stopping service thread()");
        vaccine::state = vaccine::mg_state::SHUTDOWN_REQUESTED;
        service_thread->join();
        delete service_thread;
    }

#endif

}




