import socket
import hashlib

class Client:
	def __init__(self):
		self.port = 51215
		self.hostname = globalhost

	def md5(self, fname):
		hash = hashlib.md5()
		with open(fname, "rb") as f:
			for chunk in iter(lambda: f.read(4096), b""):
				hash.update(chunk)
		return hash.hexdigest()

		
	def connect(self):
		socketobj = socket.socket()

		#hostname  = socket.gethostname()
		
		print("Connecting to the server")
		socketobj.connect((self.hostname,self.port))
		return socketobj

	def send(self,msg,regular):
		obj = self.connect()
		
		info = ""
		
		readstate = True
		print("Connected")
		obj.send(msg.encode())
		if not regular:
			infobit = obj.recv(1024).decode().split()
			if infobit[0] == "PASS":
				if msg.split()[1] == "TCP":
					filesocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
					#hostname  = socket.gethostname()
					filesocket.connect((self.hostname,int(infobit[1])))
					filesocket.send(("b").encode())

					fileread = filesocket.recv(1024).decode().split()
					print("Filename:",fileread[0],"Size:",fileread[1],"Modified time:",fileread[2:7],"MD5 hash:",fileread[7])
					filesocket.send(("R").encode())
					with open(fileread[0], 'wb') as f:
						print("File opened")
						while True:
							print("Receiving Data")
							info = filesocket.recv(1024)
							# print("Data=%s", (info))
							# print(type(info))
							if not info:
								break
							f.write(info)

					if self.md5(fileread[0]) == fileread[7]:
						print('Successfully received the file')
					else:
						print("Encountered an error while receiving")
					filesocket.close()
					print('Connection Closed')

				elif msg.split()[1] == "UDP":
					filesocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
					#hostname  = socket.gethostname()
					print("connecting to UPD port",infobit[1])
					obj.send(("b").encode())

					fileread = obj.recv(1024).decode().split()
					print("Filename:",fileread[0],"Size:",fileread[1],"Modified time:",fileread[2:7],"MD5 hash:",fileread[7])
					readsize = int(fileread[1])
					sizeread = 0
					filesocket.sendto("b".encode(), (self.hostname, int(infobit[1])))
					with open(fileread[0], 'wb') as f:
						print("File opened")
						while True:
							print("Receiving Data")
							info, udpaddr = filesocket.recvfrom(1024)
							print(info)
							sizeread += len(info)
							#print("Data=%s", (info))
							f.write(info)
							if not info or (sizeread >= readsize):
								break

					if self.md5(fileread[0]) == fileread[7]:
						print('Successfully received the file')
					else:
						print("Encountered an error while receiving")
					filesocket.close()
					print('Connection Closed')					


			else:
				return "Failed to do the task"
			obj.close()	
		else:
			infobit = obj.recv(1024).decode().split()
			if infobit[0] == "PASS":
				obj.send(("b").encode())
			else:
				return "Failed to do the task"
			cntr = int(infobit[1])
			while cntr>0:
				currrentinfo = obj.recv(1024).decode()
				cntr -= len(currrentinfo)
				info += currrentinfo
			obj.close()
			return info

globalhost=input()	
globalcount = 0
Check = "FileHash checkall"
dict={}
hashcheck = ""
hashchecksplit = []
client=Client()

while True:
	command = input()
	commandlist = command.split()
	try:
		while commandlist[0] != "Close":
			argument = True
			if commandlist[0]=="FileDownload":
				argument = False
			output = client.send(command,argument)
			#print(command,commandlist)
			if output !=None:
				print(output)
			# temp = output.split()
			#print(temp)
			for k in range(0,len(hashchecksplit),7):
				if hashchecksplit[k] not in dict.keys():
					dict[hashchecksplit[k]]=hashchecksplit[k+1]
				if dict[hashchecksplit[k]] != hashchecksplit[k+1]:
					print("Files updated in the server. Please re-download",hashchecksplit[k])		

			command = input()
			commandlist = command.split()
			if globalcount == 1 :
				hashcheck = client.send(Check,True)
				hashchecksplit = hashcheck.split() 
				pass
			globalcount = (globalcount+1)%2
		break;
	except:
		print("Some error")

