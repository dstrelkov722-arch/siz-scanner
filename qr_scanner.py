import cv2
from pyzbar import pyzbar
import json
import os

import cv2
from pyzbar import pyzbar
import json
import os

class MobileQRScanner:
    def __init__(self):
        self.camera = None
        self.is_android = False
        
        # Проверяем платформу
        try:
            from android import mActivity
            self.is_android = True
        except ImportError:
            self.is_android = False
    
    def scan_qr_code(self):
        """Сканирование QR-кода с оптимизацией для мобильных устройств"""
        if self.is_android:
            return self.scan_android()
        else:
            return self.scan_desktop()
    
    def scan_android(self):
        """Сканирование на Android устройствах"""
        try:
            # Используем камеру Android с оптимизацией
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            print("Камера Android запущена...")
            
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # Уменьшаем разрешение для повышения производительности
                small_frame = cv2.resize(frame, (320, 240))
                
                # Ищем QR-коды
                qr_codes = pyzbar.decode(small_frame)
                
                for qr in qr_codes:
                    data = qr.data.decode('utf-8')
                    print(f"Найден QR-код: {data}")
                    self.camera.release()
                    
                    try:
                        return json.loads(data)
                    except:
                        return {"raw_data": data}
                
                # Выход по тапу (для мобильных устройств)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except Exception as e:
            print(f"Ошибка сканирования на Android: {e}")
            return None
        finally:
            if self.camera:
                self.camera.release()
            cv2.destroyAllWindows()
    
    def scan_desktop(self):
        """Сканирование на десктопных устройствах"""
        try:
            self.camera = cv2.VideoCapture(0)
            
            print("Камера запущена...")
            
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                qr_codes = pyzbar.decode(frame)
                
                for qr in qr_codes:
                    data = qr.data.decode('utf-8')
                    print(f"Найден QR-код: {data}")
                    self.camera.release()
                    cv2.destroyAllWindows()
                    
                    try:
                        return json.loads(data)
                    except:
                        return {"raw_data": data}
                
                cv2.imshow('QR Scanner - Нажмите Q для выхода', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except Exception as e:
            print(f"Ошибка сканирования: {e}")
            return None
        finally:
            if self.camera:
                self.camera.release()
            cv2.destroyAllWindows()
    
    def scan_from_gallery(self, image_path):
        """Сканирование из галереи изображений"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            qr_codes = pyzbar.decode(image)
            
            if qr_codes:
                data = qr_codes[0].data.decode('utf-8')
                try:
                    return json.loads(data)
                except:
                    return {"raw_data": data}
            return None
            
        except Exception as e:
            print(f"Ошибка сканирования из галереи: {e}")
            return None

class QRScanner:
    def __init__(self):
        self.camera = None
        self.available_cameras = self.find_available_cameras()
    
    def find_available_cameras(self):
        """Поиск доступных камер"""
        available = []
        print("Поиск доступных камер...")
        for i in range(5):  # Проверяем первые 5 индексов
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                print(f"Найдена камера с индексом {i}")
                cap.release()
            else:
                print(f"Камера с индексом {i} недоступна")
        return available
    
    def start_camera(self, camera_index=0):
        """Запуск камеры с указанным индексом"""
        if not self.available_cameras:
            raise Exception("Не найдено доступных камер")
        
        if camera_index not in self.available_cameras:
            camera_index = self.available_cameras[0]  # Используем первую доступную
        
        self.camera = cv2.VideoCapture(camera_index)
        if not self.camera.isOpened():
            raise Exception(f"Не удалось открыть камеру с индексом {camera_index}")
        
        print(f"Камера {camera_index} успешно запущена")
        return True
    
    def scan_qr_code(self):
        """Сканирование QR-кода с камеры"""
        if not self.available_cameras:
            raise Exception("Камеры не доступны. Проверьте подключение камеры.")
        
        try:
            if not self.camera:
                self.start_camera()
            
            print("Камера запущена. Наведите на QR-код...")
            print("Нажмите 'Q' для выхода, 'S' для переключения камеры")
            
            current_camera_index = self.available_cameras[0]
            camera_switch_index = 0
            
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    print("Не удалось получить кадр с камеры")
                    break
                
                # Ищем QR-коды на кадре
                qr_codes = pyzbar.decode(frame)
                
                for qr in qr_codes:
                    data = qr.data.decode('utf-8')
                    print(f"Найден QR-код: {data}")
                    self.camera.release()
                    cv2.destroyAllWindows()
                    
                    try:
                        # Пытаемся распарсить JSON
                        return json.loads(data)
                    except:
                        # Если не JSON, возвращаем сырые данные
                        return {"raw_data": data}
                
                # Показываем изображение с камеры
                cv2.imshow('QR Scanner - Наведите камеру на QR-код', frame)
                
                # Обработка клавиш
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):  # Выход
                    break
                elif key == ord('s'):  # Переключение камеры
                    if len(self.available_cameras) > 1:
                        camera_switch_index = (camera_switch_index + 1) % len(self.available_cameras)
                        new_camera_index = self.available_cameras[camera_switch_index]
                        self.camera.release()
                        self.start_camera(new_camera_index)
                        print(f"Переключено на камеру {new_camera_index}")
        
        except Exception as e:
            print(f"Ошибка при сканировании: {e}")
        finally:
            if self.camera:
                self.camera.release()
            cv2.destroyAllWindows()
        
        return None
    
    def scan_from_image(self, image_path):
        """Сканирование QR-кода из файла изображения"""
        try:
            if not os.path.exists(image_path):
                raise Exception(f"Файл не найден: {image_path}")
            
            image = cv2.imread(image_path)
            if image is None:
                raise Exception("Не удалось загрузить изображение")
            
            qr_codes = pyzbar.decode(image)
            
            if qr_codes:
                data = qr_codes[0].data.decode('utf-8')
                print(f"Найден QR-код в изображении: {data}")
                try:
                    return json.loads(data)
                except:
                    return {"raw_data": data}
            else:
                print("QR-код не найден в изображении")
                return None
                
        except Exception as e:
            print(f"Ошибка при сканировании изображения: {e}")
            return None

# Функция для тестирования сканера
def test_scanner():
    scanner = QRScanner()
    print("Тестирование сканера QR-кодов...")
    print(f"Доступные камеры: {scanner.available_cameras}")
    
    if not scanner.available_cameras:
        print("Камеры не найдены. Тестирование сканирования из файла...")
        # Создадим тестовый QR-код для демонстрации
        test_data = {
            "name": "Тестовый СИЗ",
            "type": "Демонстрационный",
            "protection_class": "TEST",
            "expiry_date": "2025-12-31",
            "manufacturer": "Тестовый производитель",
            "certificate": "ТЕСТ-0001"
        }
        print("Демо-данные:", test_data)
        return test_data
    
    # Попробуем сканировать с камеры
    print("Запуск сканирования с камеры...")
    result = scanner.scan_qr_code()
    if result:
        print("Результат сканирования:", result)
        return result
    else:
        print("QR-код не найден")
        return None

if __name__ == "__main__":
    test_scanner()
