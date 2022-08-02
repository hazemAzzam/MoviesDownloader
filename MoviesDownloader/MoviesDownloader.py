from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pySmartDL import SmartDL
from threading import Thread
from PIL       import Image
from time import monotonic
from egybest   import *
import requests
import time
import sys
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

os.system("chcp 1256")

movieTextFile = 'MoviesFolderPath.txt'
if os.path.exists(movieTextFile) == False or os.stat(movieTextFile).st_size == 0:
    movieDirectory=input("Movies Director: ")
    with open(movieTextFile, 'w') as fd: 
        fd.write(movieDirectory)
else:
    with open('MoviesFolderPath.txt', 'r') as fd: 
        movieDirectory = fd.read()
        

def make_square(im, min_size=300, fill_color=(0, 0, 0, 0)):
    x, y = im.size  
    size = max(min_size, x, y)
    new_im = Image.new('RGBA', (size, size), fill_color)
    new_im.paste(im, (int((size - x) / 2), int((size - y) / 2)))
    return new_im

def assign_icon(path):
    print("Seting folder icon...", end="")
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
    os.system(f"attrib +s \"{path}\"")
    
    try:
        with open(path+"\\desktop.ini", 'w') as file:
            file.write(text)
        print(f"\r{bcolors.OKGREEN}Seting folder icon...{bcolors.ENDC}")
    except:
        print(f"\r{bcolors.FAIL}Seting folder icon...{bcolors.ENDC}")
        pass

    os.system(f"attrib +s +h \"{iniFile}\"") #hide file
   

def Download(url, path, current_size): # last stage: downloading
    headers = {"Range": f"bytes={current_size}-"}
    req = requests.get(url, stream=True, allow_redirects=True, headers=headers)
    
    if req.status_code == 404:
        print(f"{bcolors.FAIL}Error (404){bcolors.ENDC}")
        print(f"{url}")
        return False
         
    fileSize=1
     
    hasContentLength = True
    bytesToGB=9.313225746154785*(10**-10)
    
    
    res = requests.head(url)

    if 'content-length' in res.headers:
        fileSize = int(res.headers['content-length'])
        print(f"{bcolors.OKBLUE}File Size: {fileSize}  ({round(fileSize*bytesToGB, 2)}GB){bcolors.ENDC}")
    else:
        hasContentLength = False
    
    progress=current_size

    chunkSize = 1024
    percent = 100
    start = last_print = monotonic()

    with open(path, 'ab') as file:
        for chunk in req.iter_content(chunk_size=chunkSize):
            progress += file.write(chunk)
            if hasContentLength:
                now = monotonic()
                if now > last_print:
                    percent = (progress / fileSize) * 100
                    speedType = 'Kbps'
                    speed = round(progress / (now - start) / 1024)
                    
                    if speed >= 1000:
                        speedType = 'Mbps'
                        speed = round(speed / 1000, 1)
                    else:
                        speedType = 'Kbps'
    
                    print(f"\r{bcolors.OKGREEN}{progress}{bcolors.ENDC} / {fileSize} {bcolors.OKCYAN}{speed} {speedType}{bcolors.ENDC} {bcolors.OKGREEN}{round(percent, 2)}% {bcolors.ENDC} ", sep="", end="", flush=True)
                    lastSpeed = speed
    if percent < 100:
        print("\n")
        Download(url, path, progress) 
    return True

def CreateFolder(folderLocation): # Create Folder in a given path 
    exist = os.path.exists(folderLocation)
    if not exist:
        os.mkdir(folderLocation)
        return False
    return True

def checkIfFileExist(path, forceDownload=False): # check if movie already downloaded before
    if (forceDownload): # download even the file exist
        return False
    exist = os.path.exists(path)
    if not exist:
        return False
    return True

def getFileInfo(episode, quality): # get DownloadSource: Link, File Name
    print(f"Title: {episode.title}")
    print("Getting file info...", end="", flush=True)
    while(True):
        links = episode.getDownloadSources()
        length = len(links)
        if (length > 0):
            break
        print(f"\r{bcolors.WARNING}Please wait...{bcolors.ENDC}       ", sep="", end="", flush=True)
        
    print(f"\r{bcolors.OKGREEN}Getting file info...{bcolors.ENDC}")
    links.reverse()

    numberOfLinks = len(links)
    for link in links: # quality is 480 or 1080 or ...
        if(int(link.quality) <= int(quality)):
            return link
    return links[numberOfLinks - 1]
    
    

def StartThreading(episode, quality, isSeries, seriesName, seasonNumber, forceDownload):    
    filePath = ""
    fileInfo = getFileInfo(episode, quality)
    link = fileInfo.link
    fileName = fileInfo.fileName
    
    headers = requests.head(link).headers

    if 'content-length' in headers:
        fileSize = int(headers['content-length'])
    else:
        fileSize = 1

    if (isSeries): # if series make sure the directory is exists
        seriesDirectory = movieDirectory + "\\" + seriesName
        seasonsDirectory = seriesDirectory + f"\\Season {seasonNumber + 1}"        
        filePath = seasonsDirectory + "\\" + fileName

        
    else: # if not series
        movieFolder = movieDirectory + "\\" + seriesName
        if not CreateFolder(movieFolder): # if file was not exist then create and download the posture and assign it as icon
            Download(episode.posterURL, movieFolder+"\\icon.jpg", 0)
            assign_icon(movieFolder)
        else:
            print('Folder already exist\n')
            
        
        filePath = movieFolder + "\\" + fileName

    existFileSize = 0
    if (checkIfFileExist(filePath, forceDownload)): # download if movie not downloaded
        existFileSize = os.path.getsize(filePath)
        if (fileSize <= existFileSize):
            print(f"{bcolors.OKGREEN}Episode Downloaded Before.{bcolors.ENDC}")
            return
    print(f"Path: {filePath}")
    Download(link, filePath, existFileSize)
    print("\n-----")


def getEpisodeNumber(episodeTitle):
    return int(episodeTitle.split("ep-")[1].split('-')[0])

def StartEpisodesThreading(episodes, seasonNumber, start, end, quality, seriesName, forceDownload, seriesType): # Download Season
    episodes[start].refreshMetadata(True)
    posterURL = episodes[start].posterURL
    checkDirectories(seasonNumber, seriesName, posterURL, forceDownload)
    
    if getEpisodeNumber(episodes[0].title) != 1:
        episodes.reverse()


    for episodeNumber in range(start, end):
        #episodeNumber = search(episodes, i)
        episode = episodes[episodeNumber]
        episode.refreshMetadata(posterOnly = True) # refresh poster link
        
        StartThreading(episode, quality, True, seriesName, seasonNumber, forceDownload)

def printa(lista):
    for a in lista:
        print(a.title)

def checkDirectories(seasonNumber, seriesName, posterURL, forceDownload):
    print("Checking Directories...", end="")
    seriesDirectory = movieDirectory + "\\" + seriesName
    seasonsDirectory = seriesDirectory + f"\\Season {seasonNumber + 1}"
    isSeriesDirectoryExist = CreateFolder(seriesDirectory)
    CreateFolder(seasonsDirectory)
    print(f"\r{bcolors.OKGREEN}Checking Directories...{bcolors.ENDC}")
    if not isSeriesDirectoryExist or (not checkIfFileExist(seriesDirectory + "\\icon.ico", forceDownload) and not checkIfFileExist(seriesDirectory + "\\desktop.ini", forceDownload)): # download poster if not downloaded
        print("Downloading Icon...", end="")
        Download(posterURL, seriesDirectory+"\\icon.jpg")
        print(f"\r{bcolors.OKGREEN}Downloading Icon...{bcolors.ENDC}")
        assign_icon(seriesDirectory)
        print("----")

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

def printSearchResult(titles, types):
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
    printSearchResult(titles, types)
    
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
    
    if (showResult.type != "movie"):
        #print("Series..")
        if (getSeasons(showResult, quality, showTitle, forceDownload, seriesType)):
            print("Type error.")
    else:
        #print("Episode..")
        #Thread(target=StartThreading, args=(showResult, quality, False, "", 0, forceDownload, showPoster)).start()
        StartThreading(showResult, quality, False, showTitle, 0, forceDownload)
    input(f"Press {bcolors.OKCYAN}<Enter>{bcolors.ENDC} to continue.")

def getSeasons(show, quality, seriesName, forceDownload, seriesType):
    seasons = show.getSeasons()
    numberOfSeasons = len(seasons)
    print(f"[!] There are {bcolors.OKCYAN}{numberOfSeasons}{bcolors.ENDC} season")
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
        print(f"[!] There are {bcolors.OKCYAN}{numberOfEpisodes}{bcolors.ENDC} Episode")
        try:
            eStart, eEnd, eIsRanged = getRange(input("[?] Episodes: "))
            if (eStart < 0):
                return False
        except:
            return False
        
        #Thread(target=StartEpisodesThreading, args=(episodes, sStart, eStart, eEnd, quality, seriesName, forceDownload, seriesType)).start()
        StartEpisodesThreading(episodes, sStart, eStart, eEnd, quality, seriesName, forceDownload, seriesType)


        
try:
    quality = int(input(f"[?] Quality: "))
    if quality < 280:
        quality = 280
except:
    quality = 280

while(True):
    Search(quality)