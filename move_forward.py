from picrawler import Picrawler
from time import sleep

crawler = Picrawler()

times = 6
speed = 80

def move_forward():
    try:
        crawler.do_step('stand', 40)
        sleep(1.0)
        while True:
            crawler.do_action('forward', 1, speed)
            sleep(0.25)
    
    except KeyboardInterrupt:
        print("KeybordInterrupted")

    finally:
        try:
            crawler.do_step('sit', 40)
            sleep(1.0)
        except Exception as e:
            print("Failed to sit:", e)

if __name__ == "__main__":
    move_forward()
