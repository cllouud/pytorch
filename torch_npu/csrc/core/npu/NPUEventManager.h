#pragma once

#include <deque>
#include <mutex>
#include <c10/core/thread_pool.h>
#include <third_party/acl/inc/acl/acl.h>

#include "torch_npu/csrc/core/npu/NPUException.h"
namespace c10_npu {

class NPUEventManager {
public:
  static NPUEventManager& GetInstance();
  aclError QueryAndDestroyEvent();
  aclError LazyDestroy(aclrtEvent npu_event);
  void ClearEvent();
  ~NPUEventManager(){}

private:
  void run(aclrtEvent event);

private:
  std::mutex event_queue_mutex_;
  NPUEventManager();
  std::deque<aclrtEvent> npu_events_;
  std::shared_ptr<c10::TaskThreadPool> thread_pool_;
};

} // namespace c10_npu