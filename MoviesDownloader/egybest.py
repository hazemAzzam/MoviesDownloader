from bs4 import BeautifulSoup
from time import sleep
import requests
import re

baseUrl = "https://eg.egy5best.site/"

headers = {
        "referer": f"{baseUrl}/",
    }

class EgyBest:
    def __init__(self, mirror=""):
        self.baseURL = baseUrl
        
    def search(self, query):
        searchURL = f"{self.baseURL}/find/?q={query}"
        resultsList = []
        
        response = requests.get(searchURL, headers=headers, allow_redirects=True)
        soup = BeautifulSoup(response.text, "html.parser")
        
        movies = soup.find(attrs={"class": "load"}).find_all(attrs={"class": "block"})
        for movie in movies:
            movieURL = movie.get("href")
            movieImg = movie.find("img").get("src")
            movieTitle = movie.find("img").get("title").replace("مشاهدة ", "").replace("فيلم ", ""). replace(" مترجم", "").replace("شاهد ", "").replace("مدبلج ", "").replace(" عربي", "")
            movieAlt = movie.find("img").get("alt")
            if "الحلقة" in movieAlt or "الموسم" in movieAlt:
                movieTitle = movieTitle.split(" الموسم ")[0]
                movieTitle = movieTitle.split(" الحلقة ")[0]
                show = Show(movieURL, movieTitle, movieImg, "show")

                if movieTitle not in resultsList:
                    resultsList.append(show)
            else:
                resultsList.append(Episode(movieURL, 0, movieTitle, movieImg, "film"))
                
        return resultsList
            
        
class Show:
    def __init__(self, link, title=None, posterURL=None, type=None):
        self.link = link
        self.title = title
        self.posterURL = posterURL
        self.type = type
        
        self.seasonsList = []
        
    def getSeasons(self):
        response = requests.get(self.link, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        seasons = soup.find(text="المواسم").parent.parent.find_all("a")
        
        for season in seasons:
            seasonLink = season.get("href")
            seasonTitle = season.find("img").get("alt")
            seasonNumber = int(re.search(r'\d+', seasonTitle).group())
            seasonImg = season.find("img").get("src")
            
            self.seasonsList.append(Season(link=self.link, title=seasonTitle, number=seasonNumber, posterURL=seasonImg, type=self.type))
        
        return self.seasonsList
        
    def getSeasonsAsDict(self):
        seasonsDict = {}
        
        response = requests.get(self.link, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        seasons = soup.find(text="المواسم").parent.parent.find_all("a")
        
        for season in seasons:
            seasonLink = season.get("href")
            seasonTitle = season.find("img").get("alt")
            seasonNumber = int(re.search(r'\d+', seasonTitle).group())
            seasonImg = season.find("img").get("src")
            
            
            seasonObject = Season(link=seasonLink, title=seasonTitle, seasonNumber=seasonNumber, posterURL=seasonImg, type=self.type)
            
            seasonsDict[seasonNumber] = seasonObject
            
        
        return seasonsDict
        
    def __str__(self):
        return self.title
        
    def __repr__(self):
        return self.__str__()
        
    def __eq__(self, value):
        return self.__str__()
        
class Season:
    def __init__(self, link, seasonNumber, title=None, posterURL=None, type=None):
        self.link = link
        self.title = title
        self.seasonNumber = seasonNumber
        self.posterURL = posterURL
        self.type = type
        
        self.episodesList = []
        
    def getEpisodes(self):
        return list(self.getEpisodesAsDict().values())
            
    def getEpisodesAsDict(self):

        episodesDict = {}
        try:
            session = requests.Session()
            
            response = session.get(self.link, headers=headers)
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            episodes = soup.find(text=self.title).parent.parent.find_all("a")
            
            # to get episodes from the slider in the episode page
            response = session.get(episodes[0].get("href"), headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            
            episodes = soup.find(text="الحلقات").parent.parent.find_all("a")
            episodes.reverse()
            for episode in episodes:
                episodeLink = episode.get("href")
                episodeImg  = f"{baseUrl}/{episode.find('img').get('src')}"
                episodeTitle= episode.find("img").get("title")
                episodeNumber = list(map(int, re.findall(r'\d+', episodeTitle)))
                s = len(episodeNumber)

                if s == 1 or episodeNumber[0] == self.seasonNumber:
                    episode = Episode(episodeLink=episodeLink, episodeNumber=episodeNumber[s - 1], episodeTitle=episodeTitle, posterURL=episodeImg, type=self.type)
                    episodesDict[episodeNumber[s - 1]] = episode
        except Exception as exception:
            print(exception)
            
        finally:
            return episodesDict
            
        
    def __str__(self):
        return self.title
        
    def __repr__(self):
        return self.__str__()
        
    def __eq__(self, value):
        return self.__str__()
        
class Episode:
    def __init__(self, episodeLink, episodeNumber, episodeTitle, posterURL, type):
        self.link = episodeLink
        self.title = episodeTitle
        self.posterURL = posterURL
        self.type = type
        self.episodeNumber = episodeNumber
        self.downloadLinksList = []
        self.allDownloadSources = []

    def getDownloadSources(self):

        response = requests.get(self.link, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        downloadSources = soup.find_all(attrs={"class": "tr flex-start"})
        
        for downloadSource in downloadSources:
            downloadWebsite = downloadSource.find("a").text
            downloadLink = downloadSource.find("a").get("href")
       
            try:
                downloadQuality = int(downloadSource.find_all("div")[2].text.replace("p", ""))
            except:
                continue
            
            if ("تحميل" in downloadWebsite):
                self.downloadLinksList.append(DirectDownload(downloadLink, downloadQuality, self.title))
            else:
               # TODO: support other download sources
               pass
            self.allDownloadSources.append(downloadLink)

        return self.downloadLinksList
        
    def getAllDownloadSources(self):
        return self.allDownloadSources
        
    def refreshMetadata(self, posterOnly=False):
        return
        
    def __str__(self):
        return self.title
        
    def __repr__(self):
        return self.__str__()
        
    def __eq__(self, value):
        return self.__str__()
       
       

class DirectDownload:
    def __init__(self, link, quality, fileName):
        self.link = link
        self.quality = quality
        self.fileName = fileName.replace(":", "")
        self.downloadLink=""
        self.getDownloadLink()
        
    def getDownloadLink(self):
        session = requests.Session()

        response = session.get(self.link, headers=headers)
        sleep(6)
        soup = BeautifulSoup(response.text, "html.parser")
        self.link = soup.find(attrs={"id": "goNow", "class": "flex-center align-center"}).get("href")
        
    def __str__(self):
        return self.link