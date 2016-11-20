import socket, sys, threading, subprocess, os


def handle_client(soc):
	path=os.getcwd()
	try:
		while True:
			command=soc.recv(1024).split()
			if command[0]=='exit' or len(command)==0:
				break
			if command[0]=='cd':
				if command[1]=='..':
					path=os.path.abspath(os.path.join(path, os.pardir))
				elif command[1].startswith('/'):
					path=command[1]
				else:
					path+='/'+command[1]
				response=path
			else:
				try:
					result=subprocess.check_output(' '.join(command), stderr=subprocess.STDOUT, shell=True, cwd=path)
				except Exception as e:
					result=str(e)
			soc.send(result)
	except Exception as e:
		print 'ERROR: '+str(e)
	finally:
		soc.close()
		print '[-] Connection closed'


def recv_file(soc):
	buff=soc.recv(1024)
	recv_len=len(buff)
	fl_desc=open(buff.split()[0], 'wb')
	print '[*] Reciving file(%s)...' % fl_desc.name
	buff=buff.split(' ', 1)[1]
	try:
		while recv_len:
			fl_desc.write(buff)
			buff=soc.recv(4096)
			recv_len=len(buff)
			if(recv_len < 4096):
				break
		print '[*] Recived %s' % fl_desc.name
	finally:
	 	soc.close()
		fl_desc.close()
		print '[-] Connection closed'


def server_loop(port):
	server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server.bind(('localhost', port))
		server.listen(5)
		print '[*] Server started'
		while True:
			cl_soc, addr=server.accept()
			request=cl_soc.recv(1024)
			print '[+] Connection from %s:%d' % (addr[0], addr[1])
			if request=='session':
				cl_handler=threading.Thread(target=handle_client, args=(cl_soc,))
				cl_handler.start()
			elif request=='upload':
				cl_handler=threading.Thread(target=recv_file, args=(cl_soc,))
				cl_handler.start()
			elif request=='download':
				cl_handler=threading.Thread(target=send_file, args=(cl_soc,))
				cl_handler.start()
			else:
				raise Exception('Bad request: '+request)
	except Exception as e:
		print '[!] Interrupted: '+str(e)
	except KeyboardInterrupt:
		pass
	finally:
		server.close()
		print '[*] Server closed'


def start_session(addr, port):
	soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	soc.connect((addr, port))
	soc.send('session')
	try:
		while True:
			command=raw_input('pyClient:> ')
			if len(command):
				soc.send(command)
			if command=='exit':
				break
			recv_len=1
			response=''
			while recv_len:
				data=soc.recv(1024)
				recv_len=len(data)
				response+=data
				if recv_len < 1024:
					break
			print response
	finally:
		soc.close()

def upload_file(host, port, path):
	remote=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		remote.connect((host, port))
		remote.send('upload')
		print 'Sending request(upload)...'
		with open(path, 'rb') as fl_desc:
			remote.send(os.path.basename(fl_desc.name)+' ')
			remote.send(fl_desc.read())
		print 'DONE'
	finally:
		remote.close()

def download_file(host, port, path):
	print 'Downloading %s' % path
	remote=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		remote.connect((host, port))
		remote.send('download')
		if remote.recv(1024)!='download':
			return
		remote.send(os.path.basename(path))
		with open(os.path.basename(path), 'wb') as desc:
			recv_len=1
			while recv_len:
				buff=remote.recv(4096)
				desc.write(buff)
				recv_len=len(buff)
				if recv_len < 4096:
					break
		print 'Done'
	finally:
		remote.close()

def send_file(client):
	try:
		client.send('download')
		path=client.recv(1024)
		print '[*] Sending file(%s)...' % path
		with open(path, 'rb') as desc:
			client.send(desc.read())
		print '[*] File %s sent' % path
	finally:
		client.close()
		print '[-] Connection closed.'

def main():
	try:
		if sys.argv[1]=='-s':
			server_loop(int(sys.argv[2]))
		elif sys.argv[1]=='-c':
			start_session(sys.argv[2], int(sys.argv[3]))
		elif sys.argv[1]=='-u':
			upload_file(sys.argv[2], int(sys.argv[3]), sys.argv[4])
		elif sys.argv[1]=='-d':
			download_file(sys.argv[2], int(sys.argv[3]), sys.argv[4])
	except IndexError as e:
		print 'Python netcat\nUsage: python netcat.py {-s PORT | -c HOST PORT | -u HOST PORT FILE}'

if __name__=='__main__':
	main()
