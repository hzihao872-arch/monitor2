import io
import unittest

from PIL import Image

from experiments.prerequisite_probe.change_first_monitor.qwen_backend import prepare_content


class QwenAdapterTests(unittest.TestCase):
    def test_content_has_actual_images_in_order(self):
        b=io.BytesIO(); Image.new('RGB',(8,8),(2,3,4)).save(b,format='PNG')
        content=prepare_content({'prompt':'neutral','images':[b.getvalue()],
                                 'image_ids':['f0002'],'stage':'V3'})
        self.assertEqual(content[0]['text'],'neutral')
        self.assertEqual(content[-1]['type'],'image')
        self.assertEqual(content[-1]['image'].getpixel((0,0)),(2,3,4))

    def test_crop_label_includes_parent_and_time(self):
        b=io.BytesIO();Image.new('RGB',(8,8)).save(b,format='PNG')
        content=prepare_content({'prompt':'p','images':[b.getvalue()],'image_ids':['c0a'],
          'image_meta':[{'time_ms':3000,'parent_id':'f0003','crop_xyxy':[1,2,6,7]}],'stage':'V1'})
        self.assertIn('f0003',content[1]['text'])
        self.assertIn('3000',content[1]['text'])


if __name__=='__main__':unittest.main()
