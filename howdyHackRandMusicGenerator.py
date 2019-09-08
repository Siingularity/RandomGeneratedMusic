"""
Welcome to the world of RMG! or Random Music Generation.

The purpose of this program is to take general user input
about the type of piece they're looking to produce, and to
randomly generate music based on these inputs.

Don't expect the music to be too good most of the time, but
there may be that diamond in the rough that actually makes
some noise for you.

At the very least, the sound of pressing run without getting
any Debug Errors is music to my ears enough, so enjoy your song!

- Austen McGowan
- September 7th, 2019
"""
# USE PYTHON 2.7!!!!
import math
import numpy
import pyaudio
import itertools
from scipy import interpolate
from operator import itemgetter
import random


def scoreSetup():
    print("-----------------------")
    print("At any user input, you may enter R (for strings) or 0 (for numbers) to select a randomized option.")
    print("-----------------------")
    # Establishes the way the user want the score to be produced
    while True:
        # asks user for tempo
        try:
            while True:
                userTempo = int(input("Enter a numerical tempo (in BPM) for your piece -- max tempo 380 BPM --: "))
                tempo = userTempo
                if userTempo == 0: # sets the BPM to a random number if the entered tempo is 0
                    tempo = random.randint(60, 380)
                    break
                elif userTempo > 380:
                    print("Must be below 380 BPM")
                else:
                    break
            print(tempo, "BPM")
            break
        except:
            ValueError
            print("Tempo must be a number.")
    print("----------------")
    
    # converts the tempo and note value to a numerical value
    # for reference, 60bpm = 60,000ms
    tempoNumVal = tempo * 1000 # establishes the quarter note value, also the base for finding other values

    # Sets the pitches in the piece
    while True:
        userKey = raw_input("Enter the key of your piece (A, B, C, D, E, F, G): ").upper()
        allowKey = {'A', 'B', 'C', 'D', 'E', 'F', 'G'}
        if userKey == 'R': # sets the key to random
            allowKey = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
            key = random.choice(allowKey)
            break
        if userKey in allowKey:
            key = userKey
            break
        else:
            print("That is not an allowed Key")

    while True:    
        userOctave = int(input("On what octave? (1 - 7): "))
        allowOctave = {1, 2, 3, 4, 5, 6, 7}
        if userOctave == 0: # sets the octave location to random
            octave = random.randint(1, 7)
            break
        if userOctave in allowOctave:
            octave = userOctave
            break
        else:
            print("That is not an allowed Octave")

    while True:
        userMajMin = raw_input("Is the key MAJOR or MINOR?: ").upper()
        allowMajMin = {"MAJOR", "MINOR"}
        if userMajMin == 'R': # sets the scale type to random, including minor types if it is
            allowMajMin = ["MAJOR", "MINOR"]
            userMajMin = random.choice(allowMajMin)
            if userMajMin == "MINOR":
                allowMin = ["NATURAL", "HARMONIC", "MELODIC"]
                majMin = random.choice(allowMin)
                break
        if userMajMin in allowMajMin:
            if userMajMin == "MINOR":
                while True:
                    minorType = raw_input("Is it a NATURAL, HARMONIC, or MELODIC minor?: ").upper()
                    allowMinorType = {"NATURAL", "HARMONIC", "MELODIC"}
                    if minorType in allowMinorType:
                        majMin = minorType
                        break
                    else:
                        print("That is not an allowed minor type.")
                break
            else:
                majMin = userMajMin
                break
        else:
            print("Try again.")

    print(key + str(octave), majMin)

    # converting the majMin value to numerical transposition values for the code to use later
    # this establishes the key in terms of numerical whole and half steps
    if majMin == "MAJOR":
        majMin = [2, 2, 1, 2, 2, 2, 1] # 2 = whole step, 1 = half step 
    if majMin == "NATURAL":
        majMin = [2, 1, 2, 2, 1, 2, 2]
    if majMin == "HARMONIC":
        majMin = [2, 1, 2, 2, 1, 3, 1]
    if majMin == "MELODIC":
        majMin = [2, 1, 2, 2, 2, 2, 1]

    # Sets the piece duration
    while True:
        songDur = int(input("How long (in minutes) would you like your piece to be?: "))
        if songDur == 0:
            songDur = random.randint(1, 5)
            break
        if isinstance(songDur, int):
            break
        else:
            print("That is not an accepted duration.")
    print("Song duration is", songDur, "min.")
    songDur *= tempo
    songDur = int(songDur) # converts songDur to an int to make sure it repeats for an int value of times
                            # float values will cause an error, since you can't repeat '2.3333' times

    def noteSetup():
        # Establishes the accessible notes, keys, and chords
        # Credit to https://davywybiral.blogspot.com/2010/09/procedural-music-with-pyaudio-and-numpy.html

        class Note:

            # Establishing notes
            NOTES = ['c','c#','d','d#','e','f','f#','g','g#','a','a#','b']

            #  Initializing values in Note class
            def __init__(self, note, octave=7):
                self.octave = octave # Setting up how octaves work
                if isinstance(note, int):
                    self.index = note
                    self.note = Note.NOTES[note] # if 3 is passed, note is d# 
                elif isinstance(note, str): 
                    self.note = note.strip().lower()
                    self.index = Note.NOTES.index(self.note) # finds the index for the note given
            
            # sets up how transposition works
            def transpose(self, halfsteps):
                octave_delta, note = divmod(self.index + halfsteps, 12) # max amount of allowable halfsteps is 12
                return Note(note, self.octave + octave_delta)

            # turns the given note into a frequency
            # this is already set to create the proper pitches for notes
            def frequency(self):
                base_frequency = 16.35159783128741 * 2.0 ** (float(self.index) / 12.0) 
                return base_frequency * (2.0 ** self.octave)

            # returns the frequency of the note
            def __float__(self):
                return self.frequency()


            # establishes how to form scales given a root note
        class Scale:

            # sets the root to a 0 value, or the first note in the scale's array
            def __init__(self, root, intervals):
                self.root = Note(root.index, 0)
                self.intervals = intervals

            # sets up the method for cycling through intervals from a given root index
            def get(self, index):
                intervals = self.intervals
                if index < 0:
                    index = abs(index)
                    intervals = reversed(self.intervals)
                intervals = itertools.cycle(self.intervals)
                note = self.root
                for i in range(int(index)):
                    note = note.transpose(next(intervals))
                return note

            # transposes tones until it reaches an octave value
            # when an octave is reached it returns that index value
            def index(self, note):
                intervals = itertools.cycle(self.intervals)
                index = 0
                x = self.root
                while x.octave != note.octave or x.note != note.note:
                    x = x.transpose(next(intervals))
                    index += 1
                return index

            # returns the note index value + the interval it's transposed up by
            # so if A = 0, transposing a by 3 would make it C Natural
            def transpose(self, note, interval):
                return self.get(self.index(note) + interval)


            # all this stuff determines the sound of the instrument
        root = key
            # creates a sine wave for the tone
            # also sets the tempo for the piece
        def sine(frequency, length, rate):
            length = int(length * rate) # sets tempo
            factor = float(frequency) * (math.pi * 2) / rate
            return numpy.sin(numpy.arange(length) * factor)

            # takes data points and plots a graph based on the points 
            # used to determine note length and pitch
        def shape(data, points, kind='slinear'):
            items = points.items()
            sorted(items,key=itemgetter(0))
            keys = list(map(itemgetter(0), items))
            vals = list(map(itemgetter(1), items))
            interp = interpolate.interp1d(keys, vals, kind=kind)
            factor = 1.0 / len(data)
            shape = interp(numpy.arange(len(data)) * factor)
            return data * shape

            # shifts pitch upward to create harmonics
            # freq = pitch, length = note duration
            # the 44100 value sets the tempo
        def harmonics1(freq, length):
            a = sine(freq * 1.00, length, tempoNumVal)
            b = sine(freq * 2.00, length, tempoNumVal) * 0.5
            c = sine(freq * 4.00, length, tempoNumVal) * 0.125
            return (a + b + c) * 0.2

        def harmonics2(freq, length):
            a = sine(freq * 1.00, length, tempoNumVal)
            b = sine(freq * 2.00, length, tempoNumVal) * 0.5
            return (a + b) * 0.2

            # shortens duration of pitch to create plucking sound
        def pluck1(note):
            chunk = harmonics1(note.frequency(), (60000 / (1000 * float(tempo))))
            return shape(chunk, {0.0: 0.0, 0.005: 1.0, 0.25: 0.5, 0.9: 0.1, 1.0:0.0})

        def pluck2(note):
            chunk = harmonics2(note.frequency(), 2)
            return shape(chunk, {0.0: 0.0, 0.5:0.75, 0.8:0.4, 1.0:0.1})

        # creates a chord given the root (n) of the scale
        # chords are made by shifting up a 3rd, and 5th
        def chord(n, scale):
            root = scale.get(n)
            third = scale.transpose(root, 2)
            fifth = scale.transpose(root, 4)
            return pluck1(root) + pluck1(third) + pluck1(fifth)

        root = Note(root, octave)
        scale = Scale(root, majMin)
        chunks = [] # setting up the array to put our music in
        
        # actually developing the music!
        chunks.append(chord(1, scale)) # starts with tonic
        
        # repeats the code long enough to match the user song duration
        for i in range(int(songDur - 2)):
             # picks a random chord valued from 0 - 20 and adds it to the chunks array
             chunks.append(chord(random.randint(10, 26), scale))
        chunks.append(chord(1, scale))
 

        chunk = numpy.concatenate(chunks) # compresses the chunks into one list for the player to use

        # performs the piece
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=tempoNumVal, output=1)
        stream.write(chunk.astype(numpy.float32).tostring())
        stream.close()
        p.terminate()
    
    noteSetup()


scoreSetup()