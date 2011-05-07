# Query Collector GUI
import os
import sys
import subprocess
import random
import time

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)    

class Song:
    pass

class Query_Collector_GTK:
    SONG_LOC_PATH = 'TARGET SONGS'
    QUERY_LOC_PATH = 'QUERIES'

    # Types of audio files we can process
    AUDIO_TYPES = ["flac", "wav"]
    CLIP_LENGTH = 10 # seconds
    
    
    def __init__(self):
            # Set the Glade File
            self.gladefile = "Query_Collector.glade"
            self.wTree = gtk.glade.XML(self.gladefile)
            sig_dic = { 
                        "on_MainWindow_destroy" : gtk.main_quit,
                        "on_btn_set_name_clicked": self.btn_set_name_clicked,
                        "on_btn_select_song_clicked" : self.btn_select_song_clicked,
                        "on_btn_preview_clicked" : self.btn_preview_clicked,
                        "on_btn_play_and_record_clicked" : self.btn_play_and_record_clicked
                      }
            self.wTree.signal_autoconnect(sig_dic)
            
            # Access the buttons and labels
            self.btn_select_song = self.wTree.get_widget("btn_select_song")
            self.btn_preview = self.wTree.get_widget("btn_preview")
            self.btn_play_and_record = self.wTree.get_widget("btn_play_and_record")
            self.lbl_status = self.wTree.get_widget("lbl_status")
            self.lbl_selected_song = self.wTree.get_widget("lbl_selected_song")
            
            self.song = Song()
            
            # Set the names to nothing
            self.set_song_name('')
            self.set_username('')
            self.log_file = ''
            self.song_logged = False    

            self.set_status("Please Enter Your User ID")
    
    def set_username(self, username):
        self.username = username;
        if self.username == '':
            self.btn_select_song.set_sensitive(False)
        else:
            attempted_path = os.path.join(self.QUERY_LOC_PATH, username)
            if os.path.exists(attempted_path):
                dialog = gtk.MessageDialog(self.wTree.get_widget("MainWindow"), gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK_CANCEL, "This User ID has already been used, continue using it anyways?")
                dialog.set_title("Error!")
                response_id = dialog.run()
                dialog.destroy()
                if response_id == gtk.RESPONSE_CANCEL or response_id == gtk.RESPONSE_DELETE_EVENT:
                    return
                else:
                    self.QUERY_LOC_PATH = os.path.join(self.QUERY_LOC_PATH, username)
            else: 
                self.QUERY_LOC_PATH = os.path.join(self.QUERY_LOC_PATH, username)
                os.mkdir(self.QUERY_LOC_PATH)
            print "QUERY_PATH:", self.QUERY_LOC_PATH
            self.log_file = os.path.join(self.QUERY_LOC_PATH, 'song_log.txt')
            log_head = open(self.log_file, 'a')
            log_head.write("#Song Location\tQuery Location\tQuery Start (sec)\tQuery Length (sec)\n")
            log_head.close()


            self.btn_select_song.set_sensitive(True)
            self.wTree.get_widget("txt_username").set_sensitive(False)
            self.wTree.get_widget("btn_set_name").set_sensitive(False)
            
            # Crawl the directory structure for songs
            self.avail_songs = []
            directory_count = 0
            for root, dirs, files in os.walk(self.SONG_LOC_PATH):
                query_path = root.replace(self.SONG_LOC_PATH, self.QUERY_LOC_PATH)
                for dir_name in dirs:
                    directory_count += 1
                    if not os.path.exists(os.path.join(query_path, dir_name)):
                        os.mkdir(os.path.join(query_path, dir_name))
                for file_name in files:
                    if str.split( file_name, '.')[-1].lower() in self.AUDIO_TYPES:
                        self.avail_songs.append(os.path.join(root, file_name))
                    else:
                        print "Filename not usable: " + file_name
            print "# Directories: " + str(directory_count)
            print "len(self.avail_songs):", len(self.avail_songs)
            self.set_status("All Set, Click the Song Selector Button")
    
    def set_song_name(self, path_to_song):
        self.song.name = path_to_song
        if self.song.name == '':
            self.btn_preview.set_sensitive(False)
        else:
            self.btn_preview.set_sensitive(True)
        self.btn_play_and_record.set_sensitive(False)
    
    def btn_set_name_clicked(self, widget):
        print "Set Username."
        self.set_username(self.wTree.get_widget("txt_username").get_text())
    
    def btn_select_song_clicked(self, widget):
        print "Randomly Select a Song."
        
        # use "mplayer -identify 'selected_song' -sstep 999" and extract ID_LENGTH from output to determine song length
        self.song.title = ''
        self.song.artist = ''
        self.song.length = -1
        self.song.query_name = ''
        self.song_logged = False
        while self.song.length < self.CLIP_LENGTH:
            # magically pick the song, with the absolute (canonical) path
            selected_song = random.choice(self.avail_songs)
            mplayer_args = ['mplayer', '-sstep', '999', '-identify', selected_song, '-nolirc']
            mplayer_proc = subprocess.Popen(mplayer_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            mplayer_proc.stdin.write('\n')
            mplayer_proc.stdin.flush()
            # find the Title, Artist, and Length
            mplayer_output = mplayer_proc.stdout.readline()
            while (mplayer_output):
                if mplayer_output.startswith(" Artist: "):
                    self.song.artist = mplayer_output[9:-1]
                if mplayer_output.startswith(" Title: "):
                    self.song.title = mplayer_output[8:-1]
                if mplayer_output.startswith(" Name: "):
                    self.song.title = mplayer_output[7:-1]
                if mplayer_output.startswith("ID_LENGTH="):
                    self.song.length = float(mplayer_output[10:-1])
                mplayer_output = mplayer_proc.stdout.readline()
            if self.song.title == '':
                self.song.title = selected_song[selected_song.rfind('/'):-4]
        
        print selected_song
        
        # randomly select a starting location within the song to allow for CLIP_LENGTH seconds of audio
        # Since my information is only whole number of seconds in the audio file, the location chosen will
        #  Be aligned to a whole second value.
        self.song.start = random.randint(0,int(self.song.length-self.CLIP_LENGTH))
        print "Start Time:", self.song.start
        
        self.set_song_name(selected_song)
        self.lbl_selected_song.set_text(self.song.artist + ' - ' + self.song.title)
        self.song.query_name = selected_song.replace(self.SONG_LOC_PATH, self.QUERY_LOC_PATH)
        self.song.query_name = self.song.query_name[:self.song.query_name.rfind('.')] + '_Q_' + str(self.song.start) + '_' + str(self.CLIP_LENGTH) + '.wav'
        print "Query Name:", self.song.query_name
        
        self.set_status("You may now Preview the song clip and play/record your Query")
        
    def set_status(self, text):
        self.lbl_status.set_text(text)
        
    def btn_preview_clicked(self, widget):
        print "Preview Song:", self.song.name
        print "\tStart at:", self.song.start
        self.set_status("Preview now playing...")
        while gtk.events_pending(): gtk.main_iteration()
                
        # There's a bug in VLC that --start-time doesn't work with OGG files, GRRR!!!!
        player_args = ['vlc', '-I', 'dummy', '--start-time', str(self.song.start), '--run-time', str(self.CLIP_LENGTH),  self.song.name, '--play-and-exit']
        #player_args = ['mplayer', '-ss', str(self.song.start), '-endpos', str(self.CLIP_LENGTH), self.song.name]
        for arg in player_args:
            print arg,
        print ""
        player_proc = subprocess.Popen(player_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        #TODO: Disable buttons during preview
        start_time = time.time()
        while (player_proc.poll() is None):
            remaining_time = round(self.CLIP_LENGTH-time.time()+start_time, 1)
            #if remaining_time < -3:
                # problem, can we kill it?
            #    player_proc.terminate()  # crap this doesn't exist until Python 2.6, sigh
            self.set_status("Preview now playing... ~" + str(remaining_time) + 's remaining')
            while gtk.events_pending(): gtk.main_iteration()
            #player_proc.stdout.readline(1024)
            time.sleep(0.2)
        
        self.btn_play_and_record.set_sensitive(True)
        self.lbl_status.set_text("Preview finished.")
        
    def btn_play_and_record_clicked(self, widget):
        print "Play and Record:", self.song.name
        self.set_status("Recording.... Record your Query Now!")
        while gtk.events_pending(): gtk.main_iteration()
        
        # Start the song and start recording
        # There's a bug in VLC that --start-time doesn't work with OGG files, GRRR!!!!
        player_args = ['vlc', '-I', 'dummy', '--start-time', str(self.song.start), '--run-time', str(self.CLIP_LENGTH),  self.song.name, '--play-and-exit']
        #player_args = ['mplayer', '-ss', str(self.song.start), '-endpos', str(self.CLIP_LENGTH), self.song.name]
        arecord_args = ['arecord', '--duration', repr(self.CLIP_LENGTH), '--device', 'hw:1,0', '-f', 'cd', '-c', '1', '-t', 'wav', self.song.query_name]        

        player_proc = subprocess.Popen(player_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        arecord_proc = subprocess.Popen(arecord_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        
        
        #TODO: Disable all buttons during record
        start_time = time.time()
        while (player_proc.poll() is None or arecord_proc.poll() is None):
            remaining_time = round(self.CLIP_LENGTH-time.time()+start_time, 1)
            #if remaining_time < -3:
                # problem, can we kill it?
            #    player_proc.terminate() # crap this doesn't exist until Python 2.6, sigh
            self.set_status("Recording Now... ~" + str(remaining_time) + 's remaining')
            while gtk.events_pending(): gtk.main_iteration()
            time.sleep(0.2)
        
        if not self.song_logged:
            log_append = open(self.log_file, 'a')
            log_append.write(self.song.name + "\t" + self.song.query_name + "\t" + str(self.song.start) + "\t" + str(self.CLIP_LENGTH) + "\n")
            log_append.close()
            self.song_logged = True
        
        self.set_status("Recording Done.")

    def format_song_path(self, song_path):
        # strip out the SONG_LOC_PATH, and then newline the directory separators
        sp = song_path[:]
        sp = sp.replace(self.SONG_LOC_PATH + '/', '')
        sp = sp.replace('/', '\n')
        print sp
        return sp

if __name__ == "__main__":
    print "Starting Query Collector..."
    print "\tIf recording is blank use 'alsamixer -c 1' and check the capture level of the USB mic"
    query_collector_gui = Query_Collector_GTK()
    print "running gtk.main():"
    gtk.main()
    
