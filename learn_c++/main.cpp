#include <iostream>
#include <fcntl.h>
// #include <sys/ioctl.h>
#include <unistd.h>
#include <cstdint>

// LinuxカーネルのI2C定義
// #include <linux/i2c-dev.h>

// extern "C" {
//     # include <i2c/smbus.h>
// }

using namespace std;

class I2CManager{
public:
    I2CManager(const char *device, int addr){
        int fd = open(device, O_RDWR);
        if (fd < 0){
            throw runtime_error("Failed to open I2C Bus");
        }
    }
    ~I2CManager(){
        if (fd > 0){close(fd);}
    }
    void writeWordData(uint8_t reg, uint16_t value){
        int32_t result = 
    }
}