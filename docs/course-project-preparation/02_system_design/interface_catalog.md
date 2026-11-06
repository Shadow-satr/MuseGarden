# HTTP 接口目录

依据 backend/app/api/garden_preview.py 与 backend/app/schemas/garden.py；本服务不是 FastAPI，无 OpenAPI 自动文档。

|方法|路径|输入及结果|
|---|---|---|
|GET|/api/garden-preview|花园渲染数据|
|GET|/api/creations|当前预览花园创作列表|
|POST|/api/creations|garden_id、text、x、y；创建结果，成功 201|
|POST|/api/creations/{id}/music|modification_text；新版本，成功 201|
|POST|/api/creations/{id}/music-selection|audio_artifact_id；选择结果|
|POST|/api/creations/{id}/music-version-name|audio_artifact_id、display_name；重命名|
|GET|/api/audio/{id}|音频字节及其 content type|
|GET / POST|/api/music-companion/{audio_id}|读取已有解读 / 生成或读取解读|
|POST|/api/music-companion/{audio_id}/suggestions|seen_titles；修改建议|
|DELETE|/api/gardens/{garden_id}/plantings/{planting_id}|挖除种植记录|

请求模型约束：文字 1–10000 字，修改要求 1–10000 字，版本名 1–60 字；坐标为严格整数。前端输入上限另见 CreationOverlay。典型校验错误 400、未找到 404、服务异常 503，具体以路由分支为准。

## 请求及响应示意

以下 UUID 与文本均为说明用虚拟值，不是运行结果。创建请求的 JSON 结构：

```json
{"garden_id":"00000000-0000-0000-0000-000000000001","text":"今天完成了一个目标","x":22,"y":18}
```

成功结果由 CreationService.describe 构造，包含 creation_id、text、blueprint、flower、music、latest_music_version、music_versions、planting；flower 或 planting 在记录已挖除时可为 null。music 包含 artifact_id、version、url。版本项含 version_id、audio_artifact_id、version、modification_text、display_name、created_at、url、is_latest、is_selected。schema 和详情以 application/creation_service.py 为准。

错误通用格式为 `{"error": "错误描述"}`；JSON body 限制为 1–16384 字节，校验及服务异常行为按具体路由分支处理。GET 音频直接返回字节，不是 JSON。HTTP 边界将 variation_seed 整数转成十进制字符串以避免 JavaScript 精度损失。
