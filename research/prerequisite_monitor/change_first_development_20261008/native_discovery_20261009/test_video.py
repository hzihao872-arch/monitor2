from video_backend import video_times
assert video_times(15)==[.5,2.5,4.5,6.5,8.5,10.5,12.5,14.]
assert video_times(1)==[0.]
print('odd native padding and temporal checks passed')
