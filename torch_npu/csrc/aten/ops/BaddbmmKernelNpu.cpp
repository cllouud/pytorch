#include "torch_npu/csrc/framework/utils/CalcuOpUtil.h"
#include "torch_npu/csrc/framework/utils/OpAdapter.h"
#include "torch_npu/csrc/framework/utils/KernelNpuOutputSize.h"
#include "torch_npu/csrc/aten/NPUNativeFunctions.h"

namespace at_npu {
namespace native {
at::Tensor& baddbmm_nocheck(
    const at::Tensor& self,	
    const at::Tensor& tensor1,
    const at::Tensor& tensor2,
    at::Scalar beta,
    at::Scalar alpha,
    at::Tensor& result) {
  auto outputSize = baddbmm_npu_output_size(tensor1, tensor2);
  at::Tensor BatchMatMulTensor = OpPreparation::ApplyTensor(self, outputSize);

  bool isSelfT = CalcuOpUtil::IsTransposeLastTwoDims(tensor1);
  bool isMat2T = CalcuOpUtil::IsTransposeLastTwoDims(tensor2);


  OpCommand cmd;
  cmd.Name("BatchMatMul")
     .Input(tensor1)
     .Input(tensor2) 
     .Output(BatchMatMulTensor)
     .Attr("adj_x1", isSelfT)
     .Attr("adj_x2", isMat2T)
     .Run();

  at::Tensor alphaMulTensor = NPUNativeFunctions::mul(BatchMatMulTensor, alpha);
  at::Tensor betaMulTensor = NPUNativeFunctions::mul(self, beta);
  NPUNativeFunctions::add_out(alphaMulTensor, betaMulTensor, 1, result);

  return result;
}

at::Tensor& NPUNativeFunctions::baddbmm_out(
    const at::Tensor& self,	
    const at::Tensor& tensor1,
    const at::Tensor& tensor2,
    const at::Scalar& beta,
    const at::Scalar& alpha,
    at::Tensor& result){
      
  OpPreparation::CheckOut(
      {self, tensor1, tensor2},
      result,
      self);
  baddbmm_nocheck(self, tensor1, tensor2, beta, alpha, result);

  return result;
}

at::Tensor NPUNativeFunctions::baddbmm(
    const at::Tensor& self, 
    const at::Tensor& tensor1, 
    const at::Tensor& tensor2, 
    const at::Scalar& beta,
    const at::Scalar& alpha) {
  at::Tensor outputTensor = self;
  auto outputSize = baddbmm_npu_output_size(tensor1, tensor2);
  at::Tensor result = OpPreparation::ApplyTensor(outputTensor, outputSize);
  NPUNativeFunctions::baddbmm_out(self, tensor1, tensor2, beta, alpha, result);
  return result;
}

at::Tensor& NPUNativeFunctions::baddbmm_(
    at::Tensor& self, 
    const at::Tensor& tensor1, 
    const at::Tensor& tensor2, 
    const at::Scalar& beta,
    const at::Scalar& alpha) {
  c10::SmallVector<at::Tensor, N> inputs = {self, tensor1, tensor2};
  c10::SmallVector<at::Tensor, N> outputs = {self};
  CalcuOpUtil::CheckMemoryOverLaps(inputs, outputs);
    
  if (!NpuUtils::check_match(&self)) {
      at::Tensor contiguousSelf = NpuUtils::format_contiguous(self);
      at::Tensor result = NPUNativeFunctions::baddbmm_out(contiguousSelf, tensor1, tensor2, beta, alpha, contiguousSelf);
      NpuUtils::format_fresh_view(self, result);
  } else {
      NPUNativeFunctions::baddbmm_out(self, tensor1, tensor2, beta, alpha, self);
  }

  return self;
}
}
}
