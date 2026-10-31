import importlib.util
import tempfile
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).resolve().parents[1] / "skills/mr/scripts/make_mr.py"
if SCRIPT.exists():
    spec = importlib.util.spec_from_file_location("make_mr", SCRIPT)
    mr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mr)
else:
    mr = None


class AudioMixTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(mr, "MR helper must exist")

    def test_subtracts_resampled_voice_without_changing_length(self):
        sr = 48000
        t = np.arange(sr, dtype=np.float64) / sr
        mix = 0.2*np.sin(2*np.pi*440*t) + 0.3*np.sin(2*np.pi*660*t)
        vt = np.arange(44100, dtype=np.float64) / 44100
        voice = 0.2*np.sin(2*np.pi*440*vt)
        residual, details = mr.mix_accompaniment(np.column_stack((mix,mix)), sr,
                                                  np.column_stack((voice,voice)), 44100)
        self.assertEqual(residual.shape,(sr,2))
        center=residual[2400:-2400,0]
        tc=t[2400:-2400]
        voice_component=abs(np.dot(center,np.sin(2*np.pi*440*tc))*2/len(center))
        backing_component=abs(np.dot(center,np.sin(2*np.pi*660*tc))*2/len(center))
        self.assertLess(voice_component,0.002)
        self.assertAlmostEqual(backing_component,0.3,delta=0.003)
        self.assertAlmostEqual(details['gain_db'],0.0,places=6)

    def test_rejects_misaligned_or_nonfinite_audio(self):
        mix=np.zeros((48000,2),dtype=np.float32)
        with self.assertRaises(ValueError):
            mr.mix_accompaniment(mix,48000,np.zeros((35280,2),dtype=np.float32),44100)
        mix[0,0]=np.nan
        with self.assertRaises(ValueError):
            mr.mix_accompaniment(mix,48000,np.zeros((44100,2),dtype=np.float32),44100)

    def test_limits_peak_and_reports_gain(self):
        source=np.full((480,2),0.9,dtype=np.float32)
        vocal=np.full((480,2),-0.9,dtype=np.float32)
        output,details=mr.mix_accompaniment(source,48000,vocal,48000)
        self.assertLessEqual(float(np.max(np.abs(output))),0.99901)
        self.assertLess(details['gain_db'],0)

    def test_never_overwrites_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'result.mp3'
            target.write_bytes(b'existing work')
            with self.assertRaises(FileExistsError):
                mr.ensure_available(target)
            self.assertEqual(target.read_bytes(),b'existing work')

    def test_rejects_a_dangling_output_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'result.mp3'
            target.symlink_to(Path(tmp)/'missing.mp3')
            with self.assertRaises(FileExistsError):
                mr.ensure_available(target)


if __name__=='__main__':
    unittest.main()
