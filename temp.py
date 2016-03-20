import socket
import os
import time
import mimetypes
import re
import hashlib

DEbug=True

class Server:
    """Server class which servers any client connected to it"""

    def __init__(self):
        self.port = 51222
        self.sock = socket.socket()
        self.hostname = socket.gethostname()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.hostname, self.port))
        print("Hosted server :",self.hostname,'on port',self.port)
        self.alive = True
        self.availports=[51233, 51217, 51218, 51219, 50007]

    def md5(self, fname):
        hash = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash.update(chunk)
        return hash.hexdigest()

    def run(self):
        self.sock.listen(10)
        print("server listening")
        
        while self.alive:
            conn, addr = self.sock.accept()
            print(repr(addr),"connected")

            data = conn.recv(1024).decode()
            if DEbug:
                print("Recieved",repr(data))
            spdata = data.split()
            spdata+=[""]*5
            if DEbug:
                print(spdata)
            if spdata[0] == "IndexGet":
                if spdata[1] == "shortlist":
                    filelist = [ f for f in os.listdir('.') if os.path.isfile(f)]
                    info=""
                    try:
                        mint=time.mktime(time.strptime(' '.join(spdata[2:6]), '%d %m %Y %H:%M:%S'))
                        maxt=time.mktime(time.strptime(' '.join(spdata[6:10]), '%d %m %Y %H:%M:%S'))
                        for f in filelist:
                            stat = os.stat(f)
                            size = str(stat.st_size)
                            mod_t = time.ctime(stat.st_mtime)
                            cre_t = time.ctime(stat.st_ctime)
                            f_type, code = mimetypes.guess_type(f, False)
                            if not f_type:
                                f_type = "Unknown"
                            if mint<os.path.getmtime(f)<maxt:
                                info+='\t'.join([f, size, mod_t, cre_t, f_type])+'\n'
                        conn.send(("PASS "+str(len(info))).encode())
                        conn.recv(1)
                        while len(info):
                            sent=conn.send(info.encode())
                            info=info[sent:]
                    except:
                        print("Invalid command",repr(data),"recieved from",repr(addr))
                        conn.send('FAIL'.encode())
                elif spdata[1] == "longlist":
                    filelist = [ f for f in os.listdir('.') if os.path.isfile(f)]
                    info=""
                    for f in filelist:
                        stat = os.stat(f)
                        size = str(stat.st_size)
                        mod_t = time.ctime(stat.st_mtime)
                        cre_t = time.ctime(stat.st_ctime)
                        f_type, code = mimetypes.guess_type(f, False)
                        if not f_type:
                            f_type = "Unknown"
                        info+='\t'.join([f, size, mod_t, cre_t, f_type])+'\n'
                    conn.send(("PASS "+str(len(info))).encode())
                    conn.recv(1)
                    while len(info):
                        sent=conn.send(info.encode())
                        info=info[sent:]
                elif spdata[1]=="regex":
                    filelist = [ f for f in os.listdir('.') if os.path.isfile(f)]
                    info=""
                    try:
                        reprog=re.compile(' '.join(spdata[2:]))
                        for f in filelist:
                            stat = os.stat(f)
                            size = str(stat.st_size)
                            mod_t = time.ctime(stat.st_mtime)
                            cre_t = time.ctime(stat.st_ctime)
                            f_type, code = mimetypes.guess_type(f, False)
                            if not f_type:
                                f_type = "Unknown"
                            if reprog.match(f):
                                info+='\t'.join([f, size, mod_t, cre_t, f_type])+'\n'
                        conn.send(("PASS "+str(len(info))).encode())
                        conn.recv(1)
                        while len(info):
                            sent=conn.send(info.encode())
                            info=info[sent:]
                    except:
                        print("Invalid command",repr(data),"recieved from",repr(addr))
                        conn.send('FAIL'.encode())
                else:
                    print("Invalid command",repr(data),"recieved from",repr(addr))
                    conn.send("FAIL".encode())
            elif spdata[0] == "FileHash":
                if spdata[1] == "verify":
                    filename = ' '.join(spdata[2:])
                    if os.path.isfile(filename):
                        hashval=self.md5(filename)
                        mod_t = time.ctime(os.path.getmtime(filename))
                        conn.send(('PASS '+str(len(hashval)+len(mod_t)+1)).encode())
                        conn.recv(1)
                        conn.send((hashval+' '+mod_t).encode())
                    else:
                        print("Invalid command",repr(data),"recieved from",repr(addr))
                        conn.send("FAIL ".encode())                    
                elif spdata[1] == "checkall":
                    filelist = [ f for f in os.listdir('.') if os.path.isfile(f) ]
                    info=""
                    for f in filelist:
                        hashval=self.md5(f)
                        mod_t = time.ctime(os.path.getmtime(f))
                        info+=f+' '+hashval+' '+mod_t+'\n'
                    conn.send(("PASS "+str(len(info))).encode())
                    conn.recv(1)
                    while len(info):
                        sent=conn.send(info.encode())
                        info=info[sent:]
                else:
                    print("Invalid command",repr(data),"recieved from",repr(addr))
                    conn.send("FAIL".encode())                    
            elif spdata[0] == "FileDownload":
                if spdata[1]=="TCP":
                    try:
                        filename=(' '.join(spdata[2:])).strip()
                        print(filename)
                        if not os.path.isfile(filename):
                            raise(FileNotFoundError)
                        stat = os.stat(filename)
                        size = str(stat.st_size)
                        mod_t = time.ctime(stat.st_mtime)
                        hashval=self.md5(filename)
                        f=open(filename, 'rb')
                        if not len(self.availports):
                            print("No available ports to serve",repr(addr))
                            raise(IndexError)
                        transferport=self.availports.pop()
                        transfersock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        transfersock.bind((self.hostname, transferport))
                        transfersock.listen(1)
                        conn.send(("PASS "+str(transferport)).encode())
                        tconn, taddr = transfersock.accept()
                        tconn.recv(1024)
                        tconn.send((filename+'\t'+size+'\t'+mod_t+'\t'+hashval+'\n').encode())
                        tconn.recv(1)
                        with open(filename, "rb") as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                tconn.send(chunk)
                        tconn.close()
                        transfersock.close()
                        self.availports.append(transferport)
                    except IndexError:
                        print("aInvalid command",repr(data),"recieved from",repr(addr))
                        conn.send("FAIL".encode())                        
                elif spdata[1]=="UDP":
                    try:
                        filename=' '.join(spdata[2:])
                        if not os.path.isfile(filename):
                            raise(FileNotFoundError)
                        stat = os.stat(filename)
                        size = str(stat.st_size)
                        mod_t = time.ctime(stat.st_mtime)
                        hashval=self.md5(filename)
                        f=open(filename, 'rb')
                        if not len(self.availports):
                            print("No available ports to serve",repr(addr))
                            raise(IndexError)
                        transferport=self.availports.pop()
                        transfersock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        transfersock.bind((self.hostname, transferport))
                        transfersock.listen(1)
                        conn.send(("PASS "+str(transferport)).encode())
                        tconn, taddr = transfersock.accept()
                        tconn.recvfrom(1024)
                        tconn.send((filename+'\t'+size+'\t'+mod_t+'\t'+hashval+'\n').encode())
                        tconn.recvfrom(1)
                        with open(filename, "rb") as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                tconn.send(chunk)
                        tconn.close()
                        transfersock.close()
                        self.availports.append(transferport)
                    except:
                        print("bInvalid command",repr(data),"recieved from",repr(addr))
                        conn.send("FAIL".encode())                        
                else:
                    print("cInvalid command",repr(data),"recieved from",repr(addr))
                    conn.send("FAIL".encode())                    
            elif spdata[0] == "Tell":
                conn.send("PASS".encode())
                print(" ".join(spdata[1:]))
            else:
                print("Invalid command",repr(data),"recieved from",repr(addr))
                conn.send("FAIL".encode())

            conn.close()

liveserver = Server()
liveserver.run()
