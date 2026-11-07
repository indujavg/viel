import unittest
from io import BytesIO
from PIL import Image, ImageCms
from backend.images import decode_image, png_bytes, pixel_metrics

class ImagesTest(unittest.TestCase):
    def test_roundtrip_and_metrics(self):
        source = Image.new('RGB',(64,40),(100,120,140))
        restored = decode_image(png_bytes(source))
        self.assertEqual(restored.size,source.size)
        self.assertEqual(pixel_metrics(source,restored)['max_channel_change'],0)
        candidate = Image.new('RGB',source.size,(104,120,140))
        self.assertEqual(pixel_metrics(source,candidate)['max_channel_change'],4)

    def test_invalid_and_extreme_inputs(self):
        for data in [b'',b'not an image',png_bytes(Image.new('RGB',(1025,32))),png_bytes(Image.new('RGBA',(64,64))),png_bytes(Image.new('RGB',(1,1)))]:
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                decode_image(data)

    def test_wrong_decoded_format(self):
        stream=BytesIO();Image.new('RGB',(64,64)).save(stream,format='GIF')
        with self.assertRaises(ValueError):decode_image(stream.getvalue())

    def test_exif_orientation(self):
        image=Image.new('RGB',(64,40));exif=image.getexif();exif[274]=6
        stream=BytesIO();image.save(stream,format='JPEG',exif=exif)
        self.assertEqual(decode_image(stream.getvalue()).size,(40,64))

    def test_valid_color_profile_is_normalized_and_preserved(self):
        image=Image.new('RGB',(64,64),(100,120,140))
        image.info['icc_profile']=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        restored=decode_image(png_bytes(image))
        self.assertEqual(restored.getpixel((0,0)),(100,120,140))
        self.assertTrue(restored.info.get('icc_profile'))

    def test_broken_color_profile_is_rejected(self):
        image=Image.new('RGB',(64,64));image.info['icc_profile']=b'broken profile'
        with self.assertRaises(ValueError):decode_image(png_bytes(image))

    def test_opaque_alpha_png_is_accepted_but_transparency_is_rejected(self):
        image=Image.new('RGBA',(64,64),(100,120,140,255))
        restored=decode_image(png_bytes(image))
        self.assertEqual(restored.mode,'RGB')
        self.assertEqual(restored.getpixel((0,0)),(100,120,140))
        image.putpixel((0,0),(100,120,140,128))
        with self.assertRaises(ValueError):decode_image(png_bytes(image))

if __name__=='__main__':unittest.main()


