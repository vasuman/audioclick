Author   - Vasuman Ravichandran
eMail ID - vasumanar@gmail.com

Application Name - AudioClick
Version - 0.1dev

Summary:
AudioClick is a python program that attempts to correctly tag your entire music collection by fingerprinting each song and querying correct metadata online.This program makes use of Chromaprint to calculate the audio fingerprint then uses the AcoustID web service to return a MusicBrainz recording ID. The program then uses the Mutagen python library to write the metadata to the audio file's tags.

Requires:
1.Python 2.7
2.Chromaprint 0.8
3.FFmpeg
4.Mutagen
5.MusicBrainzNGS

Usage:
When in the main directory, execute the command -
$ python2.7 audioclick/ /path/to/audio/files/