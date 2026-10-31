#!/usr/bin/env python3
"""Create an MP3 accompaniment by subtracting a locally estimated vocal stem."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def ensure_available(path: Path) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"Refusing to overwrite existing output: {path}")


def mix_accompaniment(source, source_rate, vocal, vocal_rate):
    source=np.asarray(source,dtype=np.float32)
    vocal=np.asarray(vocal,dtype=np.float32)
    if source.ndim!=2 or vocal.ndim!=2 or source.shape[1]!=vocal.shape[1]:
        raise ValueError("Source and vocal must have the same number of channels")
    if not len(source) or not len(vocal) or source_rate<=0 or vocal_rate<=0:
        raise ValueError("Audio must be nonempty with positive sample rates")
    if not np.isfinite(source).all() or not np.isfinite(vocal).all():
        raise ValueError("Audio contains nonfinite samples")
    if abs(len(source)/source_rate-len(vocal)/vocal_rate)>0.02:
        raise ValueError("Vocal stem and source durations differ by over 20 ms")
    if vocal_rate!=source_rate:
        factor=math.gcd(source_rate,vocal_rate)
        vocal=resample_poly(vocal,source_rate//factor,vocal_rate//factor,axis=0)
    adjustment=len(source)-len(vocal)
    if abs(adjustment)>2:
        raise ValueError("Vocal stem length differs after resampling; refusing to time-stretch")
    if adjustment>0:
        vocal=np.pad(vocal,((0,adjustment),(0,0)))
    residual=source-vocal[:len(source)]
    peak=float(np.max(np.abs(residual)))
    gain=min(1.0,0.999/max(peak,1e-12))
    residual*=gain
    return residual,{'source_frames':len(source),'output_frames':len(residual),
                     'sample_rate':source_rate,'gain_db':20*math.log10(gain),
                     'rounding_adjustment_frames':adjustment,'time_stretched':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path,help='Local audio file, e.g. downloaded YouTube audio')
    parser.add_argument('--output',required=True,type=Path,help='New MP3 path; existing files are never overwritten')
    parser.add_argument('--threads',type=int,default=4,help='CPU threads for Demucs (default: 4)')
    args=parser.parse_args()
    if args.output.suffix.lower()!='.mp3':
        parser.error('--output must end in .mp3')
    if args.threads<1:
        parser.error('--threads must be positive')
    if not args.input.is_file():
        parser.error('input audio file does not exist')
    ensure_available(args.output)
    args.output.parent.mkdir(parents=True,exist_ok=True)

    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model
    from demucs.separate import load_track

    torch.set_num_threads(args.threads)
    torch.manual_seed(0)
    with tempfile.TemporaryDirectory(prefix='suno-mr-') as tmp:
        source_path=Path(tmp)/'source.wav'
        intermediate=Path(tmp)/'accompaniment.wav'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(args.input),
                        '-vn','-ar','48000','-ac','2','-c:a','pcm_f32le',str(source_path)],check=True)
        print('Loading Demucs htdemucs_ft vocal checkpoint; first use may download model weights.',flush=True)
        model=get_model('04573f0d')
        model.eval()
        wav=load_track(source_path,model.audio_channels,model.samplerate)
        ref=wav.mean(0)
        mean,std=ref.mean(),ref.std()
        if not torch.isfinite(std) or float(std)<1e-8:
            raise ValueError('Source is silent or invalid')
        wav=(wav-mean)/std
        with torch.inference_mode():
            stems=apply_model(model,wav[None],device='cpu',shifts=1,split=True,
                              overlap=0.25,progress=True)[0]
        vocal=(stems[model.sources.index('vocals')]*std+mean).cpu().numpy().T
        original,rate=sf.read(source_path,dtype='float32',always_2d=True)
        backing,details=mix_accompaniment(original,rate,vocal,model.samplerate)
        sf.write(intermediate,backing,rate,subtype='PCM_24')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(intermediate),
                        '-af','volume=-1dB','-c:a','libmp3lame','-b:a','320k',
                        '-map_metadata','-1',str(args.output)],check=True)
    details.update({'input':str(args.input.resolve()),'output':str(args.output.resolve()),
                    'model':'Demucs htdemucs_ft vocal component 04573f0d',
                    'mp3_additional_gain_db':-1.0,
                    'quality':'Listen for residual voice and instrumental melody; separation is not perfect.'})
    print(json.dumps(details,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
