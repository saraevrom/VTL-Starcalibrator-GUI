import numpy as np
from .filepool import RandomFileAccess
from vtl_common.common_GUI.tk_forms_assist import FormNode, IntNode, AlternatingNode, FloatNode, ArrayNode, OptionNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from vtl_common.localization import get_locale
from noise.noising import FloatDistributedAlter
from track_gen import generate_track, LinearTrack, GaussianPSF, TriangularLightCurve
from track_gen.pdm_params import side_a, side_b

class TrackSource(object):
    def get_track(self, filelist:RandomFileAccess, rng, frame_size):
        raise NotImplementedError("Cannot obtain track")

    def uses_files(self):
        return False


class GeneratorError(Exception):
    def __init__(self,txt):
        super().__init__(txt)

###Source: file list

class FileTrackSource(TrackSource):
    def __init__(self, shift_threshold):
        self.shift_threshold = shift_threshold

    def uses_files(self):
        return True

    def get_track(self, filelist:RandomFileAccess, rng, frame_size):
        filelist.set_shift_threshold(self.shift_threshold)
        return filelist.random_access(rng, frame_size)[0]

class FileTrackSourceForm(FormNode):
    DISPLAY_NAME = get_locale("teacher.form.trackgen.file")
    FIELD__shift_threshold = create_value_field(IntNode, get_locale("teacher.form.trackgen.file.threshold"),32)

    def get_data(self):
        data = super().get_data()
        return FileTrackSource(**data)

### Source: random generator
class GeneratorTrackSource(TrackSource):
    def __init__(self, velocity, a, psf, min_len, max_len, start_energy, t_peak, subframes, time_cap=None):
        # PARAMETERS:
        # velocity: distributed velocity
        self.velocity_sampler = velocity
        self.a_sampler = a
        self.start_energy_sampler = start_energy
        self.psf_sampler = psf
        self.t_peak_sampler = t_peak
        self.min_len = min_len
        self.max_len = max_len
        self.subframes = subframes
        self.time_cap = time_cap

    def get_track(self, filelist:RandomFileAccess, rng, frame_size):
        attempts = 10000
        while attempts>0:
            speed = self.velocity_sampler.sample(rng)
            psf = self.psf_sampler.sample(rng)
            a = self.a_sampler.sample(rng)
            t_peak = self.t_peak_sampler.sample(rng) # 0.0=start of track, 1.0=end of track
            x0 = (rng.random()*2-1)*side_a/2
            y0 = (rng.random()*2-1)*side_b/2
            phi0 = (rng.random()*2-1)*np.pi
            e_min = self.start_energy_sampler.sample(rng)
            trajectory = LinearTrack(x0, y0, phi0, speed, a)
            if self.time_cap is None:
                t_peak = t_peak*trajectory.length(frame_size) # Modify t_peak according to track length
            else:
                t_peak = t_peak * trajectory.length(min(frame_size, self.time_cap)) # Modify t_peak according to track length
            lc = TriangularLightCurve(t_peak, 1.0, e_min)
            psf = GaussianPSF(psf,psf)
            if self.min_len<=trajectory.length(frame_size)<=self.max_len:
                track, actual_duration = generate_track(trajectory,lc,psf, frame_size, self.subframes,
                                                        time_cap=self.time_cap)
                # nans=np.logical_or.reduce(np.isnan(track),axis=(1,2))
                #print(track[0])
                #print("NAN WARN", nans)
                assert not np.isnan(track).any()

                assert track.shape[0]>=actual_duration
                if track.shape[0]>actual_duration:
                    shift = rng.integers(low=0,high=track.shape[0]-actual_duration)
                else:
                    shift = 0


                return np.roll(track,shift, axis=0)
            attempts-=1
        raise RuntimeError("Expired attempts for track generation")


class CapOption(OptionNode):
    DISPLAY_NAME = get_locale("teacher.form.trackgen.random.duration")
    ITEM_TYPE = create_value_field(FloatDistributedAlter, "")

class GeneratorTrackSourceForm(FormNode):
    DISPLAY_NAME = get_locale("teacher.form.trackgen.random")
    FIELD__velocity = create_value_field(FloatDistributedAlter, get_locale("teacher.form.trackgen.random.speed"))
    FIELD__a = create_value_field(FloatDistributedAlter, get_locale("teacher.form.trackgen.random.a"))
    FIELD__t_peak = create_value_field(FloatDistributedAlter, get_locale("teacher.form.trackgen.random.t_peak"))
    FIELD__psf = create_value_field(FloatDistributedAlter, get_locale("teacher.form.trackgen.random.psf"))
    FIELD__start_energy = create_value_field(FloatDistributedAlter, get_locale("teacher.form.trackgen.random.start_energy"))
    FIELD__min_len = create_value_field(FloatNode, get_locale("teacher.form.trackgen.random.length.min"),4.0)
    FIELD__max_len = create_value_field(FloatNode, get_locale("teacher.form.trackgen.random.length.max"),16.0)
    FIELD__subframes = create_value_field(IntNode, get_locale("teacher.form.trackgen.random.subframes"), 10)
    FIELD__time_cap = CapOption

    def get_data(self):
        kwargs = super().get_data()
        return GeneratorTrackSource(**kwargs)


class ShuffleSource(TrackSource):
    def __init__(self, sourcelist):
        weights = np.array([item["weight"] for item in sourcelist])
        self.probabilities = weights/np.sum(weights)
        self.sources = [item["generator"] for item in sourcelist]

    def uses_files(self):
        if not self.sources:
            return False
        return self.sources[0].uses_files()

    def get_track(self, filelist:RandomFileAccess, rng, frame_size):
        #print("SOURCES:", self.sources)
        if self.sources:
            src = rng.choice(self.sources, p=self.probabilities)
            return src.get_track(filelist, rng, frame_size)
        else:
            raise GeneratorError("No generators are set up")

class GeneratorEntry(FormNode):
    DISPLAY_NAME = get_locale("teacher.form.trackgen.generator")
    FIELD__weight = create_value_field(FloatNode, get_locale("teacher.form.trackgen.weight"), 1.0)
    FIELD__generator = GeneratorTrackSourceForm


class GeneratorArray(ArrayNode):
    DISPLAY_NAME = get_locale("teacher.form.trackgen.generators")
    ITEM_TYPE = GeneratorEntry

    def get_data(self):
        data = super().get_data()
        print("GOT DATA")
        return ShuffleSource(data)

class TrackGeneratorField(AlternatingNode):
    DISPLAY_NAME = get_locale("teacher.form.trackgen")
    SEL__filelist = FileTrackSourceForm
    SEL__random = GeneratorArray