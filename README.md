# SlideCast File Generator
This is continuation work from [slidecast](https://slidecast.github.io/). This tool allows unfamiliar users to create a zipped sld file without going through recorder from a normal mp4 video file.
This tool is built on simple Django webframe work with only two views (one being download request)
## Installation
1. All requirements are listed in requirements.txt. (All of the following commands are executed in project folder)
2. Make requirements.txt executable if it is not using following command 
```bash
chmod +x requirements.txt
```
3. To install all the python dependencies, run the following command,
```bash
pip3 install -r requirements.txt
```
4. To setup the server, 
```bash
python3 manage.py runserver
```
## Usage
1. navigate to [http://127.0.0.1:8000/mp42sld/](http://127.0.0.1:8000/mp42sld/)
1. Paste a youtube link or upload a video file of a lecture video
2. set all required parameters - audio bit rate : 20k is enough for decent audibility. sensitivity and freq are set to optimal according to our test files
3. click convert and wait till download option appears. Click download to get zipped sld file and you may play it on locally installed progressive web application of slidecast