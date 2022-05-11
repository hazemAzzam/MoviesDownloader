from pySmartDL import SmartDL
from threading import Thread
from PIL       import Image
from egybest   import *
import progressbar
import requests
import time
import os

os.system("chcp 1256")

movieTextFile = 'MoviesFolderPath.txt'
if os.path.exists(movieTextFile) == False or os.stat(movieTextFile).st_size == 0:
    movieDirectory=input("Movies Director: ").replace('\\','\\\\')
    with open(movieTextFile, 'w') as fd: 
        fd.write(movieDirectory)
else:
    with open('MoviesFolderPath.txt', 'r') as fd: 
        movieDirectory = fd.read()

threads = [] # start 
ready = [] # start -> ready
running = [] # ready -> running
MAX_THREADS = 2
s = requests.session()
def make_square(im, min_size=300, fill_color=(0, 0, 0, 0)):
    x, y = im.size  
    size = max(min_size, x, y)
    new_im = Image.new('RGBA', (size, size), fill_color)
    new_im.paste(im, (int((size - x) / 2), int((size - y) / 2)))
    return new_im

def assign_icon(path):
    print("Seting folder icon...")
    text = """[ViewState]
Mode=
Vid=
FolderType=Videos
Logo=
[.ShellClassInfo]
IconResource=icon.ico,0"""
    filename = path + "\\icon.jpg"
    iconFile = path + "\\icon.ico"
    iniFile = path + "\\desktop.ini"
    img = Image.open(filename)
    img = make_square(img)
    icon_sizes = [(256,256)]
    img.save(iconFile, sizes=icon_sizes)
    
    os.system(f"attrib -s \"{path}\"")
    os.system(f"attrib +s +h \"{iconFile}\"") #hide file
    os.system(f"del \"{filename}\"") 
    os.system(f"attrib +s \"{path}\"")
    
    try:
        with open(path+"\\desktop.ini", 'w') as file:
            file.write(text)
    except:
        print("error setting folder icon")
        pass
    os.system(f"attrib +s +h \"{iniFile}\"") #hide file
    
    
def Download(url, path): # last stage: downloading
    print("Downloading...")
    try:
        req = requests.get(url, stream=True, allow_redirects=True)
        res = requests.head(url)
        fileSize=1
        isContentLength = True
        try:
            fileSize = int(res.headers['content-length'])
            print(f"File Size: {fileSize}  ({round(fileSize*10**-9,2)}GB)")
        except:
            isContentLength = False
  
        progress=0
        chunkSize = 1000

        with open(path, 'wb') as file:
            for chunk in req.iter_content(chunk_size=chunkSize):
                file.write(chunk)
                if isContentLength:
                    progress = progress + chunkSize
                    percent = (progress / fileSize) * 100
                    print(f"\r{progress} / {fileSize}  {round(percent, 2)}% ", sep="", end="", flush=True)

    except:
        print("Error (404)")
    
    print("----")
    
    #print("\n")
    #obj = SmartDL(url, path)
    #obj.start()

def CreateFolder(folderLocation): # Create Folder in a given path 
    exist = os.path.exists(folderLocation)
    if not exist:
        os.mkdir(folderLocation)

def checkIfFileExist(path, forceDownload=False): # check if movie al ready downloaded before
    if (forceDownload): # download even the file exist
        return False
    exist = os.path.exists(path)
    if not exist:
        return False
    return True

def getFileInfo(episode, quality): # get DownloadSource: Link, File Name
    print("Getting file info...")
    #print(f"{episode.title}")
    while(True):
        links = episode.getDownloadSources()
        length = len(links)
        if (length > 0):
            break
        print("\rWaiting links...")
        time.sleep(1)
    print("File info collected...")
    links.reverse()

    numberOfLinks = len(links)
    for link in links: # quality is 480 or 1080 or ...
        if(int(link.quality) <= int(quality)):
            return link
    return links[numberOfLinks - 1]
    
    

def StartThreading(episode, quality, isSeries, seriesName, seasonNumber, forceDownload, posterURL):
    print(episode.title)
    
    fileInfo = getFileInfo(episode, quality)
    link = fileInfo.link
    filePath = ""
    fileName = fileInfo.fileName
    fileSize = int(requests.head(link).headers['content-length'])
    if (isSeries): # if series make sure the directory is exists
        print("Checking Directories...")
        seriesDirectory = movieDirectory + "\\" + seriesName
        seasonsDirectory = seriesDirectory + f"\\Season {seasonNumber + 1}"
        filePath = seasonsDirectory + "\\" + fileName
        CreateFolder(seriesDirectory)
        CreateFolder(seasonsDirectory)

        if (not checkIfFileExist(seriesDirectory + "\\icon.ico", forceDownload) and not checkIfFileExist(seriesDirectory + "\\desktop.ini", forceDownload)): # download poster if not downloaded
            Download(posterURL, seriesDirectory+"\\icon.jpg")
            assign_icon(seriesDirectory)

        
    else: # if not series
        filePath = movieDirectory + "\\" + fileName

    print(f"{filePath}")
    if (checkIfFileExist(filePath, forceDownload)): # download if movie not downloaded
        existFileSize = os.path.getsize(filePath)
        if (fileSize <= existFileSize):
            print("Episode Downloaded Before ^^\n-----")
            return
    Download(link, filePath)

def StartEpisodesThreading(episodes, seasonNumber, start, end, quality, seriesName, forceDownload, seriesType): # Download Season
    #episodes.sort(key=attrgetter('title'))

    #printa(episodes)
    for episodeNumber in range(start, end):
        #episodeNumber = search(episodes, i)
        episode = episodes[episodeNumber]
        episode.refreshMetadata(posterOnly = True) # refresh poster link
        posterURL = episode.posterURL
        
        StartThreading(episode, quality, True, seriesName, seasonNumber, forceDownload, posterURL)

def search(lista, episodeNumber):
    for i in range(0, len(lista)):
        number = int(lista[i].title.split('ep-')[1].split('-')[0])
        if number == episodeNumber:
            return number

def printa(lista):
    for a in lista:
        print(a.title)

def StartSeasonsThreading(seasons, start, end, quality, seriesName, forceDownload, seriesType):
    length = len(seasons)
    for seasonNumber in range(start, end):
        episodes = seasons[seasonNumber].getEpisodes()
        numberOfEpisodes = len(episodes)
        StartEpisodesThreading(episodes, seasonNumber,0, numberOfEpisodes, quality, seriesName, forceDownload, seriesType)

def getRange(range):
    rangeList = range.split('-')
    if(len(rangeList) > 1):
        start = int(rangeList[0]) - 1
        end = int(rangeList[1])
        return start, end, True
    else:
        start = int(rangeList[0]) - 1
        end = start + 1
        return start, end, False

def get_max_str(lst, fallback=''):
    return max(lst, key=len) if lst else fallback

def printList(titles, types):
    maxTitleLength = len(get_max_str(titles))
    maxTypeLength = len(get_max_str(types))
    for i in range(0, len(titles)):
        print("    "+"-" * (maxTitleLength + maxTypeLength + 1))
        print("    "+f"{titles[i]}" + " "* (maxTitleLength-len(titles[i])) + " "*(maxTypeLength-len(types[i])) +f" {types[i]}")
    print("    "+"-" * (maxTitleLength + maxTypeLength + 1))

def Search(quality):
    os.system("cls")
    forceDownload = False
    title = input("[?] Search: ")
    egybest = EgyBest()
    searchResult = egybest.search(title)
    length = len(searchResult)
    if (length == 0):
        return
    titles = []
    types = []
    for i in range(0, length):
        titles.append(f"{i+1}. " + searchResult[i].title)
        types.append(searchResult[i].type + f" ({searchResult[i].rating})")
    printList(titles, types)
    
    try:
        selectedShow = int(input("[?] Open: ")) - 1
        if (selectedShow < 0):
            return
    except:
        return

    seriesType = searchResult[selectedShow].type
    showTitle = searchResult[selectedShow].title.replace(":", "") 
    showResult = searchResult[selectedShow]
    showPoster = searchResult[selectedShow].posterURL
    #print(showResult.type)
    if (showResult.type != "movie"):
        print("Series..")
        if (not getSeasons(showResult, quality, showTitle, forceDownload, seriesType)):
            return 
    else:
        print("Episode..")
        #Thread(target=StartThreading, args=(showResult, quality, False, "", 0, forceDownload, showPoster)).start()
        StartThreading(showResult, quality, False, "", 0, forceDownload, showPoster)

def getSeasons(show, quality, seriesName, forceDownload, seriesType):
    seasons = show.getSeasons()
    numberOfSeasons = len(seasons)
    print(f"[!] There are {numberOfSeasons} season")
    try:
        sStart, sEnd, sIsRanged = getRange(input("[?] Season: "))
        if(sStart < 0):
            return False
    except:
        return False
    if (sIsRanged):
        #Thread(target=StartSeasonsThreading, args=(seasons, sStart, sEnd, quality, seriesName, forceDownload, seriesType)).start()
        StartSeasonsThreading(seasons, sStart, sEnd, quality, seriesName, forceDownload, seriesType)
    else:
        episodes = seasons[sStart].getEpisodes()
        numberOfEpisodes = len(episodes)
        print(f"[!] There are {numberOfEpisodes} Episode")
        try:
            eStart, eEnd, eIsRanged = getRange(input("[?] Episodes: "))
            if (eStart < 0):
                return False
        except:
            return False
        
        #Thread(target=StartEpisodesThreading, args=(episodes, sStart, eStart, eEnd, quality, seriesName, forceDownload, seriesType)).start()
        StartEpisodesThreading(episodes, sStart, eStart, eEnd, quality, seriesName, forceDownload, seriesType)


        
try:
    quality = int(input("[?] Quality: "))
    if quality < 280:
        quality = 280
except:
    quality = 280

while(True):
    Search(quality)