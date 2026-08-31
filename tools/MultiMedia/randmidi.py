#  Copyright (c) 2025-2026. L.J.Afres, All rights reserved.
import random
import mido

def generate_random_music(length=100):
    new_midi = mido.MidiFile()
    track = mido.MidiTrack()
    new_midi.tracks.append(track)

    for _ in range(length):
        note = random.randint(60, 72)
        velocity = random.randint(64, 127)
        duration = random.randint(32, 96)
        track.append(mido.Message('note_on', note=note, velocity=velocity, time=0))
        track.append(mido.Message('note_off', note=note, velocity=velocity, time=duration))

    return new_midi

# random_music = generate_random_music()
# random_music.save('random_music.mid')


midi_file = mido.MidiFile("random_music.mid")
def analyze_notes(midi_file):
    note_counts = {}
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'note_on':
                note_counts[msg.note] = note_counts.get(msg.note, 0) + 1
    return note_counts

note_distribution = analyze_notes(midi_file)
print(note_distribution)
