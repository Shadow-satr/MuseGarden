# 有证据的技术问题

- 前端数字精度：HTTP 边界将 63 位 variation_seed 转为十进制字符串，依据 backend/app/api/garden_preview.py。
- 种植空间：大花九格不能全部合法时降级为小花，中心冲突则拒绝，依据 application/garden_planting.py。
- 本次构建环境：系统临时目录删除被拒，使用项目内临时目录构建成功，见测试日志。

开发者亲身经历、问题发生时间和个人体会仍需本人核实，不应从代码推断。
