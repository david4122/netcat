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


def server_loop(port):
	server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server.bind(('localhost', port))
		server.listen(5)
		print '[*] Server started'
		while True:
			cl_soc, addr=server.accept()
			print '[+] Connection from %s:%d' % (addr[0], addr[1])
			cl_soc.send('Python netcat server')
			cl_handler=threading.Thread(target=handle_client, args=(cl_soc,))
			cl_handler.start()
	except Exception as e:
		print '[!] Interrupted: '+str(e)
	finally:
		server.close()
		print '[*] Server closed'


def connect(addr, port):
	soc=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	soc.connect((addr, port))
	print soc.recv(1024)
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


def main():
	try:
		if sys.argv[1]=='-s':
			server_loop(int(sys.argv[2]))
		elif sys.argv[1]=='-c':
			connect(sys.argv[2], int(sys.argv[3]))
	except IndexError as e:
		print 'Python netcat\nUsage: python netcat.py {-s PORT | -c HOST PORT}'

if __name__=='__main__':
	main()
