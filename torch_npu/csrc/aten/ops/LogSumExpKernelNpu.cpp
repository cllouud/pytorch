#include <ATen/WrapDimUtilsMulti.h>
#include <ATen/NamedTensorUtils.h>

#include "torch_npu/csrc/framework/utils/OpAdapter.h"
#include "torch_npu/csrc/aten/NPUNativeFunctions.h"

namespace at_npu {
namespace native {

c10::SmallVector<int64_t, SIZE> logsumexp_npu_output_size(
    const at::Tensor& self,
    at::IntArrayRef dims,
    bool keepdim) {
  return reduce_ops_npu_output_size(self, dims, keepdim);
}

at::Tensor squeeze_multiple(const at::Tensor& self, at::IntArrayRef dims) {
  int ndims = self.sizes().size();
  auto dims_to_squeeze = at::dim_list_to_bitset(dims, ndims);
  at::Tensor result = self;
  for (int i = ndims - 1; i >= 0; --i) {
    if (dims_to_squeeze[i]) {
      result = result.squeeze(i);
    }
  }
  return result;
}

at::Tensor& logsumexp_out_nocheck(const at::Tensor& self, at::IntArrayRef dims, bool keepdim, at::Tensor& result) {
  at::NoNamesGuard guard;
  if (self.numel() != 0) {
    OpCommand cmd;
    auto maxes = NPUNativeFunctions::amax(self, dims, true);
    auto maxes_squeezed = (keepdim ? maxes : squeeze_multiple(maxes, dims));
    maxes_squeezed.masked_fill_(maxes_squeezed.abs() == INFINITY, 0);
    cmd.Name("ReduceLogSumExp")
        .Input(self.sub(maxes))
        .Input(dims)
        .Output(result)
        .Attr("keep_dims", keepdim)
        .Run();
    result.add_(maxes_squeezed);
  } else {
    at::sum_out(result, at::exp(self), dims, keepdim);
    result.log_();
  }
  at::namedinference::propagate_names_for_reduction(result, self, dims, keepdim);
  return result;
}

at::Tensor& NPUNativeFunctions::logsumexp_out(const at::Tensor& self, at::DimnameList dims, bool keepdim, at::Tensor& result) {
  return logsumexp_out(self, dimnames_to_positions(self, dims), keepdim, result);
}

at::Tensor& NPUNativeFunctions::logsumexp_out(const at::Tensor& self, at::IntArrayRef dims, bool keepdim, at::Tensor& result) {
  auto outputSize = logsumexp_npu_output_size(self, dims, keepdim);
  OpPreparation::CheckOut(
      {self},
      result,
      self,
      outputSize);
  return logsumexp_out_nocheck(self, dims, keepdim, result);
}

at::Tensor NPUNativeFunctions::logsumexp(const at::Tensor& self, at::IntArrayRef dims, bool keepdim) {
  auto outputSize = logsumexp_npu_output_size(self, dims, keepdim);
  at::Tensor result =  OpPreparation::ApplyTensor(self, outputSize);
  return logsumexp_out_nocheck(self, dims, keepdim, result);
}

at::Tensor NPUNativeFunctions::logsumexp(const at::Tensor& self, at::DimnameList dims, bool keepdim) {
  return logsumexp(self, dimnames_to_positions(self, dims), keepdim);
}

} // namespace native
} // namespace at_npu