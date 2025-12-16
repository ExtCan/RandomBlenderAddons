/*
 * Blender Compatibility Layer Header
 *
 * This header provides compatibility shims between Blender 2.79 API
 * and modern Blender versions for the render engine.
 */

#ifndef BLENDER_COMPAT_H
#define BLENDER_COMPAT_H

#ifdef __cplusplus
extern "C" {
#endif

/* Forward declarations for Blender types */
typedef struct Scene Scene;
typedef struct Render Render;
typedef struct RenderData RenderData;
typedef struct RenderResult RenderResult;
typedef struct Object Object;
typedef struct Material Material;
typedef struct Tex Tex;
typedef struct World World;
typedef struct Lamp Lamp;
typedef struct Image Image;
typedef struct Camera Camera;

/* Compatibility functions */

/**
 * Initialize the compatibility layer
 * Must be called before using any render engine functions
 */
void blender_compat_init(void);

/**
 * Shutdown the compatibility layer
 */
void blender_compat_shutdown(void);

/**
 * Translate modern Blender scene data to 2.79 format
 */
Scene *blender_compat_translate_scene(void *modern_scene);

/**
 * Free translated scene data
 */
void blender_compat_free_scene(Scene *scene);

/**
 * Get render settings from modern Blender
 */
RenderData *blender_compat_get_render_data(void *modern_scene);

/**
 * Allocate render result compatible with modern Blender
 */
RenderResult *blender_compat_alloc_render_result(int width, int height);

/**
 * Transfer render result to modern Blender
 */
void blender_compat_transfer_render_result(void *modern_result, RenderResult *old_result);

/**
 * Free render result
 */
void blender_compat_free_render_result(RenderResult *result);

#ifdef __cplusplus
}
#endif

#endif /* BLENDER_COMPAT_H */
