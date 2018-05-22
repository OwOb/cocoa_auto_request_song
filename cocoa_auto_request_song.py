from bs4 import BeautifulSoup
import requests
import random
import time


def toSec(t) :
    time, sec = t.split(':'), 0
    for i in time :
        sec *= 60
        sec += int(i)
    #del time
    return sec

def toTime(s) :
    return '%02d:'%(s//3600)+'%02d:'%(s//60%60)+'%02d'%(s%60)

def nowTime() :
    return time.strftime("%Y/%m/%d %H:%M:%S > ", time.gmtime(time.time()+28800))

def request(s) :
    while (1) : #重複嘗試
        try :
            r = requests.get(s)
            return r
        except :
            print(nowtime()+'request error : '+s)

def waitTime(soup) :
    nowPlayTime = soup.find(id='timerPosition').text.split('/')
    delayTime = toSec(nowPlayTime[1])-toSec(nowPlayTime[0])
    if len(soup.find_all('br')) == 7 or len(soup.find_all('a')) != len(soup.find_all('li')) : #等待點播中
        for songInRequest in soup.find_all('tr') :
            if songInRequest.find('a') or songInRequest.find('br') :
                break
            delayTime += toSec(songInRequest.find_all('td')[7].text)
    #del nowPlayTime
    return delayTime
    


#更新歌單函數
def updata() :
    
    global allSong, zero, lastTime
    allSong.clear()
    #del zero[:]
    print(nowTime()+'開始更新歌單...')
    
    r = request('http://acgmusic.ddns.net:4095/ajax/zh_status.html') #獲取songList
    soup = BeautifulSoup(r.text, 'html.parser')
    songListNameList, songCount, songTag = [songListIndex.text for songListIndex in soup.find_all('li')], 0, ['name', 'artist', 'series', 'playedTime', 'songTime', 'codec']
    #del r, soup
    
    songListId = 1
    for songListName in songListNameList : #依序搜尋songList
        print(nowTime()+'正在更新... ('+songListName+')')
        songId, page = 0, 0
        while 1 : #持續換page搜尋
            r = request('http://acgmusic.ddns.net:4095/ajax/zh_songlist.html?list_id='+str(songListId)+'&page='+str(page))
            soup = BeautifulSoup(r.text, 'html.parser')
            songArray = soup.find_all('tr')
            if len(songArray) == 0 : #該songList已搜尋完
                #del r, soup, songArray
                break
            for song in songArray : #依序紀錄歌曲
                songData = [songDetail.text for songDetail in song.find_all('td')]
                allSong[(songListId, songId)] = dict(zip(songTag, songData[2:]))
                if songData[5] == '0' : #點播0次的歌曲
                    zero.append((songListId, songId))
                songCount, songId = songCount+1, songId+1
                #del songData
            page += 1
            #del songArray, r, soup
        songListId += 1
        #del songId, page
    lastTime = time.time()
    f = open('cocoa_songlist.txt','w',encoding='utf-8')
    f.write(str(allSong))
    f.write('\n'+str(lastTime)+'\n')
    f.close
    print(nowTime()+'歌單更新完成 (共 '+str(songCount)+' 首)  OwO')
    #del songListNameList, songCount, songTag, songListId


#系統啟動
print(nowTime()+'心愛台自動點播系統啟動~~~')


#初始化資料
try :
    lastTime, f = 0, open('cocoa_songlist.txt','r',encoding='utf-8')
    allSong, zero, lastTime = eval(f.readline()), [], int(f.readline().split('.')[0])
    for key in allSong :
        if allSong[key]['playedTime'] == '0' :
            zero.append(key)
    print(nowTime()+'載入記錄成功!!')

except :
    allSong, zero, lastTime = {}, [], 0
    print(nowTime()+'載入記錄失敗...')

if lastTime != 0 :
    f.close()


#主迴圈
while 1 :

    r = request('http://acgmusic.ddns.net:4095/ajax/zh_status.html')
    soup = BeautifulSoup(r.text, 'html.parser')
    
    
    if time.time()-lastTime > 86400 : #初次啟動程式or超過24hr沒更新歌單
        print(nowTime()+'初次啟動程式 or 超過24hr沒更新歌單...')
        #del r, soup
        updata()
        continue
    
    
    if len(soup.find_all('br')) == 7 or len(soup.find_all('a')) != len(soup.find_all('li')) : #點播歌曲仍在點播列中
        print(nowTime()+'點播歌曲仍在點播列中... (歌曲重播、播放MAD...等等)')
        delayTime = waitTime(soup)
        #del r, soup
        print(nowTime()+'等待 '+toTime(delayTime)+' 後重新申請點播...')
        time.sleep(delayTime)
        #del delayTime
        continue
    
    
    if len(soup.find_all('tr')) >= 21 : #歌單已滿
        print(nowTime()+'歌單已滿...  Q Q')
        delayTime = waitTime(soup)
        #del r, soup
        print(nowTime()+'等待 '+toTime(delayTime)+' 後重新申請點播...')
        time.sleep(delayTime)
        #del delayTime
        continue
    
    
    #點播歌曲
    requestSongId = random.choice(zero)
    print(nowTime()+'申請點播歌曲 ['+allSong[requestSongId]['name']+'] (list='+str(requestSongId[0])+' id='+str(requestSongId[1])+')')
    #del r, soup
    
    request('http://acgmusic.ddns.net:4095/played.html?cmd=request&list_id='+str(requestSongId[0])+'&song_id='+str(requestSongId[1]))
    r = request('http://acgmusic.ddns.net:4095/ajax/zh_status.html')
    soup = BeautifulSoup(r.text, 'html.parser')
    
    if len(soup.find_all('br')) == 6 and len(soup.find_all('a')) == len(soup.find_all('li')) : #點播失敗
        print(nowTime()+'點播歌曲失敗...  QAQ')
        #del requestSongId, r, soup
        print(nowTime()+'準備重新嘗試...')
        continue
    
    #點播成功
    print(nowTime()+'點播歌曲成功~~~  OwO')
    delayTime = waitTime(soup)
    #del requestSongId, r, soup
    print(nowTime()+'等待 '+toTime(delayTime)+' 後重新申請點播...')
    
    if delayTime > 1800 : #等待時間超過30min
        print(nowTime()+'等待時間超過 30min 準備更新歌單...')
        updataBeginTime = time.time()
        updata()
        updataEndTime = time.time()
        delayTime = delayTime-int(updataEndTime-updataBeginTime)
        #del updataBeginTime, updataEndTime
        print(nowTime()+'等待 '+toTime(delayTime)+' 後重新申請點播...')
    
    time.sleep(delayTime)
    #del delayTime
