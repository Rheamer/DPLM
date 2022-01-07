import socket

def server():
	host = socket.gethostname()   # get local machine name
	print('Host:', host)
	port = 8080  # Make sure it's within the > 1024 $$ <65535 range

	s = socket.socket()
	# s.bind((host, port))
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	
	s.bind(('', port))
  	
	s.listen(1)
	print('Listening...')
  
	client_socket, adress = s.accept()
	print("Connection from: " + str(adress))
	print('client_socket:', client_socket)
	
	while True:
		data = client_socket.recv(1024).decode('utf-8')

		#if not data:
			#break
		if data == '\r\n':
			continue
		if data == '':
			continue
		print('From online user: ' + data)
		# print('Type:', type(data))
		data = data.upper()
		# data = data + '\r'
		client_socket.send(data.encode('utf-8'))
  
	print('Closing connection')
	client_socket.close()


if __name__ == '__main__':
	server()
