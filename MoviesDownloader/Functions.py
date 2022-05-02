from multiprocessing import Process
from genericpath import exists
from threading import Thread
from egybest import *
import threading
import requests
import time
import os

movieDirectory = "D:\\Movies"
threads = [] # start 
ready = [] # start -> ready
running = [] # ready -> running
MAX_THREADS = 2

def Download(url, path, workerID): # last stage: downloading
    #print("Downloading")
    req = requests.get(url, stream=True)
    with open(path, 'wb') as file:
        for chunk in req.iter_content(chunk_size=128):
            file.write(chunk)
    thread = threads[workerID]
    threads.remove(thread)
    #running.remove(thread)

    print(f"Worker {workerID} finished")
    

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
    while(True):
        links = episode.getDownloadSources()
        length = len(links)
        if (length > 0):
            break
        print("waiting links")

    links.reverse()

    numberOfLinks = len(links)
    for link in links: # quality is 480 or 1080 or ...
        if(int(link.quality) <= int(quality)):
            return link
    
    

def StartThreading(episode, quality, isSeries, seriesName, seasonNumber, forceDownload, workerID):
    print(f"Worker {workerID} fetching Links...")
    fileInfo = getFileInfo(episode, quality)
    print(f"Worker {workerID} got links")
    link = fileInfo.link
    fileName = fileInfo.fileName
    print(f"Worker {workerID} start Downloading")
    if (isSeries): # if series make sure the directory is exists
        seriesDirectory = movieDirectory + "\\" + seriesName
        seasonsDirectory = seriesDirectory + f"\\Season {seasonNumber + 1}"
        filePath = seasonsDirectory + "\\" + fileName
        CreateFolder(seriesDirectory)
        CreateFolder(seasonsDirectory)
        if (not checkIfFileExist(filePath, forceDownload)): # download if file not downloaded
            Download(link, filePath, workerID)
            #thread = Thread(target=Download, args=(link, filePath, workerID))
            #while len(threads) >= MAX_THREADS:
            #    pass
            #threads.append(thread)
            #thread.start()
    else: # if not series
        filePath = movieDirectory + "\\" + fileName
        Download(link, filePath, workerID)

def StartEpisodesThreading(episodes, seasonNumber, start, end, quality, seriesName, forceDownload, workerID): # Download Season
    episodes.reverse()
    step = 1
    if start > end:
        step = -1

    for episodeNumber in range(start, end, step):
        episode = episodes[episodeNumber]
        thread = Thread(target=StartThreading, args=(episode, quality, True, seriesName, seasonNumber, forceDownload, len(threads)))
        thread.start()

def StartSeasonsThreading(seasons, start, end, quality, seriesName, forceDownload, workerID):
    length = len(seasons)
    step = 1
    if start > end:
        step = -1
    for seasonNumber in range(start, end, step):
        episodes = seasons[seasonNumber].getEpisodes()
        numberOfEpisodes = len(episodes)
        StartEpisodesThreading(episodes, seasonNumber,0, numberOfEpisodes, quality, seriesName, forceDownload, workerID)

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


def Search(quality):
    os.system("cls")
    forceDownload = False
    title = input("[?] Search: ")
    egybest = EgyBest()
    searchResult = egybest.search(title)
    length = len(searchResult)
    if (length == 0):
        return
    for i in range(0, length):
        print(f"    {i+1}. {searchResult[i].title}  ({searchResult[i].type})")
    
    try:
        while (True):
            selectedShow = int(input("[?] Open: ")) - 1
            if (selectedShow < 0):
                return
            if (selectedShow < length):
                break
    except:
        print("Error (2)")
        return

    showTitle = searchResult[selectedShow].title
    showTitle = showTitle.replace(":", "")
    showResult = searchResult[selectedShow]
    
    if (type(showResult) == Show):
        if (not getSeasons(showResult, quality, showTitle, forceDownload)):
            return 
    else:
        thread = Thread(target=StartThreading, args=(showResult, quality, False, "", 0, forceDownload, len(threads)))
        #threads.append(thread)
        thread.start()

def getSeasons(show, quality, seriesName, forceDownload):
    seasons = show.getSeasons()
    numberOfSeasons = len(seasons)
    print(f"[!] There are {numberOfSeasons} season")
    try:
        while (True):
            sStart, sEnd, sIsRanged = getRange(input("[?] Season: "))
            if(sStart < 0):
                return False
            if (sStart < numberOfSeasons):
                    break
    except:
        print("Error (3)")
        return False
    if (sIsRanged):
        thread = Thread(target=StartSeasonsThreading, args=(seasons, sStart, sEnd, quality, seriesName, forceDownload, len(threads)))
        #threads.append(thread)
        thread.start()
    else:
        episodes = seasons[sStart].getEpisodes()
        numberOfEpisodes = len(episodes)
        print(f"[!] There are {numberOfEpisodes} Episode")
        try:
            while (True):
                eStart, eEnd, eIsRanged = getRange(input("[?] Episodes: "))
                if (eStart < 0):
                    return False
                if (eStart < numberOfEpisodes):
                    break
        except:
            print("error (4)")
            return False
        thread = Thread(target=StartEpisodesThreading, args=(episodes, sStart, eStart, eEnd, quality, seriesName, forceDownload, len(threads)))
        #threads.append(thread)
        thread.start()


def threadsController():
    while(True):
        while len(threads) == 0: 
            pass
        
        while len(running) == MAX_THREADS:
            pass

        for thread in threads: # threads -> ready
            ready.append(thread)

        currentWorking = len(running)
        readyWorkers = len(ready)
        requiredWorkers = MAX_THREADS - currentWorking

        while requiredWorkers != 0 and readyWorkers != 0: # ready -> running
            requiredWorkers = requiredWorkers - 1
            thread = ready[0]
            running.append(thread)
            ready.remove(thread)
            readyWorkers = readyWorkers - 1
            thread.start()

        
        
                    
            
    
Process(target=threadsController).start()
os.system("chcp 1256")
quality = int(input("[?] Quality: ")) or 240
while(True):
    try:
        Search(quality)
    except:
        print("Error(1)")
        Search(quality)