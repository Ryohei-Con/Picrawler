#include <iostream>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <cstdint>

// LinuxカーネルのI2C定義
#include <linux/i2c-dev.h>

extern "C" {
    # include <i2c/smbus.h>
}

using namespace std;

class I2CManager{
public:
    I2CManager(const char *device, int addr){
        fd = open(device, O_RDWR);
        cout << fd << endl;
        if (fd < 0){
            throw runtime_error("Failed to open I2C Bus");
        }
        if (ioctl(fd, I2C_SLAVE, addr) < 0){
            close(fd);
            throw runtime_error("Failed to acquire bus access/talk to slave");
        }
    }
    ~I2CManager(){
        if (fd > 0){close(fd);}
    }
    void writeWordData(uint8_t reg, uint16_t value){
        int32_t result = i2c_smbus_write_word_data(fd, reg, value);
        if (result < 0){
            perror("Write word data failed");
        }
    }
private:
    int fd;
};

int main(){
    try{
        I2CManager i2c("/dev/i2c-1", 0x14);
        i2c.writeWordData(0x44, 0xFF0F);
        sleep(1);
        i2c.writeWordData(0x40, 0x5F01);
        sleep(1);
        i2c.writeWordData(0X23, 0XA401);
        sleep(1);
        i2c.writeWordData(0X23, 0X3301);
        sleep(1);
        i2c.writeWordData(0x23, 0x0000);
        sleep(1);
    }catch(const exception& e){
        cout << e.what() << endl;
    }
    return 0;
}