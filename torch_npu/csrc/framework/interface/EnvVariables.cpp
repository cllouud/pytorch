#include <limits.h>
#include "torch_npu/csrc/core/npu/NPUException.h"

#include "third_party/acl/inc/acl/acl_mdl.h"
#include "torch_npu/csrc/framework/utils/ForceJitCompileList.h"
#include "torch_npu/csrc/framework/interface/AclOpCompileInterface.h"
#include "torch_npu/csrc/framework/aoe/AoeUtils.h"
#include "torch_npu/csrc/core/npu/npu_log.h"
#include "torch_npu/csrc/core/npu/register/OptionRegister.h"
namespace at_npu {
namespace native {
namespace env {

void ValidPathCheck(const std::string& file_path) {
  char abs_path[PATH_MAX] = {'\0'};
  if (realpath(file_path.c_str(), abs_path) == nullptr) {
    TORCH_CHECK(0, "configPath path Fails, path ", (char*)file_path.c_str());
  }
}

REGISTER_OPTION_HOOK(autotune, [](const std::string& val) {
  if (val == "enable") {
    at_npu::native::aoe::aoe_manager().EnableAoe();
  }
})

REGISTER_OPTION_HOOK(autotunegraphdumppath, [](const std::string& val) {
    ValidPathCheck(val);
    at_npu::native::aoe::aoe_manager().SetDumpGraphPath(val);
})

REGISTER_OPTION_INIT_BY_ENV(bmmv2_enable)
REGISTER_OPTION_BOOL_FUNCTION(CheckBmmV2Enable, bmmv2_enable, "0", "1")

REGISTER_OPTION_HOOK(mdldumpswitch, [](const std::string &val){
  if (val == "enable") {
    aclmdlInitDump();
  } else {
    aclmdlFinalizeDump();
  }
})
REGISTER_OPTION_HOOK(mdldumpconfigpath, [](const std::string &val) {
  aclmdlSetDump(val.c_str());
})

REGISTER_OPTION_HOOK(jitCompile, [](const std::string &val) {
  AclSetCompileopt(aclCompileOpt::ACL_OP_JIT_COMPILE, val.c_str());
})
REGISTER_OPTION_BOOL_FUNCTION(CheckJitDisable, jitCompile, "enable", "disable")

REGISTER_OPTION_HOOK(ACL_OP_DEBUG_LEVEL, [](const std::string &val) {
  AclSetCompileopt(aclCompileOpt::ACL_OP_DEBUG_LEVEL, val.c_str());
})
REGISTER_OPTION_HOOK(ACL_DEBUG_DIR, [](const std::string &val) {
  AclSetCompileopt(aclCompileOpt::ACL_DEBUG_DIR, val.c_str());
})

REGISTER_OPTION_HOOK(ACL_OP_COMPILER_CACHE_MODE, [](const std::string &val) {
  AclSetCompileopt(aclCompileOpt::ACL_OP_COMPILER_CACHE_MODE, val.c_str());
})

REGISTER_OPTION_HOOK(ACL_OP_COMPILER_CACHE_DIR, [](const std::string &val) {
  AclSetCompileopt(aclCompileOpt::ACL_OP_COMPILER_CACHE_DIR, val.c_str());
})

REGISTER_OPTION_HOOK(ACL_PRECISION_MODE, [](const std::string &val) {
  auto ret = AclSetCompileopt(aclCompileOpt::ACL_PRECISION_MODE, val.c_str());
  TORCH_CHECK(ret == ACL_SUCCESS,
              "Failed to set compile option ACL_PRECISION_MODE, result = ", ret, ", set value ", val);
})

REGISTER_OPTION_HOOK(ACL_OP_SELECT_IMPL_MODE, [](const std::string &val) {
  auto ret = AclSetCompileopt(aclCompileOpt::ACL_OP_SELECT_IMPL_MODE, val.c_str());
  TORCH_CHECK(ret == ACL_SUCCESS,
              "Failed to set compile option ACL_OP_SELECT_IMPL_MODE, result = ", ret, ", set value ", val);
})

REGISTER_OPTION_HOOK(ACL_OPTYPELIST_FOR_IMPLMODE, [](const std::string &val)
                      { AclSetCompileopt(aclCompileOpt::ACL_OPTYPELIST_FOR_IMPLMODE, val.c_str()); })
REGISTER_OPTION_HOOK(NPU_FUZZY_COMPILE_BLACKLIST, [](const std::string &val)
                      { ForceJitCompileList::GetInstance().RegisterJitlist(val); })

REGISTER_OPTION(MM_BMM_ND_ENABLE)
REGISTER_OPTION_BOOL_FUNCTION_UNIQ(CheckMmBmmNDDisable, MM_BMM_ND_ENABLE, "enable", "disable")

REGISTER_OPTION(ALLOW_INTERNAL_FORMAT)
REGISTER_OPTION_BOOL_FUNCTION_UNIQ(CheckForbidInternalFormat, ALLOW_INTERNAL_FORMAT, "enable", "disable")

REGISTER_OPTION_HOOK(ALLOW_CONV_HF32, [](const std::string &val) {
  static const std::string mm_hf32_option_name = "ALLOW_MATMUL_HF32";
  auto mm_hf32_val = c10_npu::option::GetOption(mm_hf32_option_name);
  // default value is False;
  std::string mm_hf32 = "0";
  if (mm_hf32_val.has_value() && (mm_hf32_val.value() == "enable")) {
    mm_hf32 = "1";
  }

  std::string conv_hf32 = (val == "enable") ? "1" : "0";
  std::string allow_hf32 = conv_hf32 + mm_hf32;
  auto ret = AclSetCompileopt(aclCompileOpt::ACL_ALLOW_HF32, allow_hf32.c_str());
  TORCH_CHECK(ret == ACL_SUCCESS,
              "Failed to set compile option ACL_ALLOW_HF32, result = ", ret, ", set value ", allow_hf32);
  ASCEND_LOGD("Set ACL option ACL_ALLOW_HF32 value to %s.", allow_hf32.c_str());
})

REGISTER_OPTION_HOOK(ALLOW_MATMUL_HF32, [](const std::string &val) {
  static const std::string conv_hf32_option_name = "ALLOW_CONV_HF32";
  auto conv_hf32_val = c10_npu::option::GetOption(conv_hf32_option_name);
  // default value is True;
  std::string conv_hf32 = "1";
  if (conv_hf32_val.has_value() && (conv_hf32_val.value() == "disable")) {
    conv_hf32 = "0";
  }

  std::string mm_hf32 = (val == "enable") ? "1" : "0";
  std::string allow_hf32 = conv_hf32 + mm_hf32;
  auto ret = AclSetCompileopt(aclCompileOpt::ACL_ALLOW_HF32, allow_hf32.c_str());
  TORCH_CHECK(ret == ACL_SUCCESS,
              "Failed to set compile option ACL_ALLOW_HF32, result = ", ret, ", set value ", allow_hf32);
  ASCEND_LOGD("Set ACL option ACL_ALLOW_HF32 value to %s.", allow_hf32.c_str());
})

} // namespace env
} // namespace native
} // namespace at_npu
