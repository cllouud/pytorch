#include "NPUTdtChannel.h"
namespace c10_npu {
bool NpuTdtChannel::Init() {
  std::lock_guard<std::mutex> lock(channel_mutex_);
  if (inited_) {
    TORCH_NPU_WARN("Current channel %s has beed inited.", channel_name_);
    return true;
  }
  TORCH_CHECK(!channel_name_.empty(), "Name of channel is empty.");
  TORCH_CHECK(capacity_ != 0, "Capacity of cur %s is zero.", channel_name_);
  NPU_CHECK_ERROR(aclrtGetDevice(&device_id_));
  channel_handle_ = acl_tdt::AcltdtCreateChannelWithCapacity(
      device_id_, channel_name_.c_str(), capacity_);
  
  TORCH_CHECK(channel_handle_ != nullptr, "Init channel failed.");
  inited_ = true;
  return inited_;
}

NpuTdtChannel::~NpuTdtChannel() {
  std::lock_guard<std::mutex> lock(channel_mutex_);
  if (inited_) {
    TORCH_CHECK(channel_handle_ != nullptr, "channel_handle is nullptr during ~NpuTdtChannel");
    auto ret = acl_tdt::AcltdtDestroyChannel(channel_handle_);
    TORCH_CHECK(ret == ACL_ERROR_NONE,
                "Destroy channel ", channel_name_,
                " failed, error message is ", acl::AclGetErrMsg());
    channel_handle_ = nullptr;
    inited_ = false;
  }
}

std::shared_ptr<TdtDataSet> NpuTdtChannel::Dequeue() {
  std::lock_guard<std::mutex> lock(channel_mutex_);
  if (!inited_) {
    return nullptr;
  }
  TORCH_CHECK(channel_handle_ != nullptr, "channel_handle is nullptr during Dequeue");
  auto ret_dataset = std::make_shared<TdtDataSet>();
  auto ret = acl_tdt::AcltdtReceiveTensor(channel_handle_, 
                                          ret_dataset->GetPtr().get(), 
                                          time_out_);
  TORCH_CHECK((ret == ACL_ERROR_NONE) || (ret == ACL_ERROR_RT_QUEUE_EMPTY),
              "Dequeue channel ", channel_name_,
              " failed, error message is ", acl::AclGetErrMsg());
  return ret_dataset;
}
} // namespace c10_npu

