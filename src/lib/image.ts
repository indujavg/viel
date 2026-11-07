export const MAX_BYTES = 10 * 1024 * 1024;
export const MAX_PIXELS = 24_000_000;

export function validateFile(file: { type: string; size: number }): string | null {
  if (!['image/png', 'image/jpeg'].includes(file.type)) return 'Choose a PNG or JPEG image.';
  if (file.size === 0) return 'This file is empty.';
  if (file.size > MAX_BYTES) return 'Choose an image smaller than or equal to 10 MB.';
  return null;
}

export function validateDimensions(width: number, height: number): string | null {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return 'This image has invalid dimensions.';
  if (width * height > MAX_PIXELS) return 'Choose an image with at most 24 megapixels.';
  return null;
}
