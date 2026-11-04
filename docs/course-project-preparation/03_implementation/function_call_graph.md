# 调用链

HTTP POST /api/creations → CreationService.create_memory → plan_planting → run_creation_pipeline → MusicGenerationService.generate_for_revision → 存储与花朵生命周期 → GardenService.plant_flower → DemoCreationStore.save。顺序及分支以 application/creation_service.py 为准。
