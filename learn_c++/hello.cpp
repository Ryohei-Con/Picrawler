# include <iostream>
# include <fcntl.h>

using namespace std;
int main(){
    int fd = open("example.txt", O_RDONLY);
    char buffer[128];
    ssize_t bytesRead = read(fd, buffer, sizeof(buffer) - 1);
    cout << bytesRead << endl;
    if (bytesRead >= 0){
        // buffer[bytesRead] = '\0';

        cout << "----File Content----" << endl;
        cout << buffer << endl;
        cout << "--------------------" << endl;
    }else{
        cerr << "Read Error: " << strerror(errno) << endl;
    }
    close(fd);
    return 0;
}