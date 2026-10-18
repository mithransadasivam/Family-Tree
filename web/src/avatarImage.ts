const SIZE = 320
const MAX_INPUT_BYTES = 15 * 1024 * 1024

/** Centre-crop any picture the browser can decode to a square JPEG (~320px, a few tens of KB). */
export async function toAvatarJpeg(file: File): Promise<Blob> {
  if (!file.type.startsWith('image/')) throw new Error('Please choose an image file.')
  if (file.size > MAX_INPUT_BYTES) throw new Error('That picture is too large. Please choose one under 15 MB.')
  let bitmap: ImageBitmap
  try {
    bitmap = await createImageBitmap(file)
  } catch {
    throw new Error('That picture could not be read. Try a JPEG or PNG.')
  }
  try {
    const side = Math.min(bitmap.width, bitmap.height)
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = SIZE
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Your browser cannot process pictures.')
    ctx.fillStyle = '#fff' // JPEG has no transparency
    ctx.fillRect(0, 0, SIZE, SIZE)
    ctx.imageSmoothingQuality = 'high'
    ctx.drawImage(bitmap, (bitmap.width - side) / 2, (bitmap.height - side) / 2, side, side, 0, 0, SIZE, SIZE)
    const blob = await new Promise<Blob | null>((res) => canvas.toBlob(res, 'image/jpeg', 0.88))
    if (!blob) throw new Error('Could not prepare that picture.')
    return blob
  } finally {
    bitmap.close()
  }
}
