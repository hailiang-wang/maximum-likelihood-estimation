#!/usr/bin/env python
# -*- coding: utf-8 -*-
import functools
import math # we import a standard python library for mathematics
import numpy # import the NumPy library to work with NumPy arrays of class numpy.ndarray
import scipy.sparse # import the Sparse package for SciPy for sparse matrices


class LogRegError(Exception):
    '''
    The exception class that we generate, if something goes wrong in the logistic regression.
    '''


    def __init__(self, error_msg=None):
        """ 
        A class constructor that is called automatically when creating class objects.
         : Param error_msg - The error message that we want to send, throwing an exception.
        """
        self.msg = error_msg

    def __str__(self):
        """A standard method that is called automatically when printing objects of a class using the print function.
         : Return Returns the string to print: an error message common to logistic regression,
         And an additional message passed as the constructor argument (see comment to the constructor).
         """
        error_msg = 'Logistic regression algorithm is incorrect!'
        if self.msg is not None:
            error_msg += (' ' + self.msg)
        return error_msg


class LogisticRegression:
    """ Класс для классификатора на основе алгоритма логистической регрессии. """

    def __init__(self):
        """ Конструктор класса, вызываемый автоматически при создании объектов класса.
        В конструкторе мы инициализируем все атрибуты класса "пустыми" значениями.
        """
        self.__a = None  # атрибут класса, который будет свободным членом логистической регрессии
        self.__b = None  # атрибут класса, который будет numpy.ndarray-массивом коэффициентов логистической регрессии
        self.__th = None  # атрибут класса, который будет вероятностным порогом для классификации

    def save(self, file_name):
        """ Сохранить все параметры логистической регрессии (атрибуты класса) в текстовый файл.
        :param file_name - строка с названием текстового файла, в который будут записаны сохраняемые параметры.
        """
        # сначала проверяем, есть ли что сохранять
        if (self.__a is None) or (self.__b is None) or (self.__th is None):
            # если атрибуты класса пустые, т.е. сохранять нечего, то генерируем исключение
            raise LogRegError('Parameters have not been specified!')
        # открываем текстовый файл для записи
        with open(file_name, 'w') as fp:
            # записываем размер входного вектора признаков
            fp.write('Input size {0}\n\n'.format(self.__b.shape[0]))
            # записываем коэффициенты логистической регрессии
            for ind in range(self.__b.shape[0]):
                fp.write('{0}\n'.format(self.__b[ind]))
            # записываем свободный член и вероятностный порого
            fp.write('\n{0}\n\n{1}\n'.format(self.__a, self.__th))

    def load(self, file_name):
        """ Загрузить все параметры логистической регрессии из текстового файла в атрибуты класса.
        :param file_name - строка с названием текстового файла, из которого будут читаться загружаемые параметры.
        """
        # открываем текстовый файл для чтения
        with open(file_name, 'r') as fp:
            input_size = -1  # размер входного вектора признаков (пока не прочитан, считается равным -1)
            cur_line = fp.readline()  # читаем первую строку
            ind = 0  # счётчик количества прочитанных параметров логистической регрессии
            while len(cur_line) > 0:  # до тех пор, пока очередная строка не пуста, т.е. файл ещё не закончился
                prepared_line = cur_line.strip()  # удаляем лишние пробелы из начала и конца строки
                if len(prepared_line) > 0:  # если после удаления пробелов строка не пуста, то пытаемся её распарсить
                    if input_size <= 0:  # если размер входного вектора признаков ещё не прочитан, то читаем его
                        parts_of_line = prepared_line.split()
                        if len(parts_of_line) != 3:
                            raise LogRegError('Parameters cannot be loaded from a file!')
                        if (parts_of_line[0].lower() != 'input') or (parts_of_line[1].lower() != 'size'):
                            raise LogRegError('Parameters cannot be loaded from a file!')
                        input_size = int(parts_of_line[2])
                        if input_size <= 0:
                            raise LogRegError('Parameters cannot be loaded from a file!')
                        self.__b = numpy.zeros(shape=(input_size,), dtype=numpy.float)
                        self.__a = 0.0
                        self.__th = 0.5
                    else:  # если размер входного вектора признаков был уже прочитан, то читаем сами параметры регрессии
                        if ind > (input_size + 1):  # в файле оказалось слишком много информации, это ошибка
                            raise LogRegError('Parameters cannot be loaded from a file!')
                        if ind < input_size:  # читаем ind-й коэффициент логистической регрессии из input_size штук
                            self.__b[ind] = float(prepared_line)
                        elif ind == input_size:  # читаем свободный член логистической регрессии
                            self.__a = float(prepared_line)
                        else:  # читаем вероятностный порог (он не должен быть меньше 0 или больше 1)
                            self.__th = float(prepared_line)
                            if (self.__th < 0.0) or (self.__th > 1.0):
                                raise LogRegError('Parameters cannot be loaded from a file!')
                        ind += 1  # благополучно прочитали очередной параметр, и теперь увеличиваем счётчик
                cur_line = fp.readline()  # читаем очередную строку из файла
            if ind <= (input_size + 1):
                raise LogRegError('Parameters cannot be loaded from a file!')

    def transform(self, X):
        """ Вычислить вероятности отнесения входных объектов к первому классу.
        :param X - двумерный numpy.ndarray-массив, описывающий векторы признаков входных объектов
        (одна строка - один вектор признаков, количество строк равно количеству входных объектов,
        количество столбцов равно количеству признаков объекта).
        :return одномерный numpy.ndarray-массив, описывающий вероятности отнесения входных объектов к первому классу
        (число элементов этого массива равно количеству строк матрицы X, т.е. количеству входных объектов).
        """
        # проверить, что параметры логистической регресии (коэффициенты и свободный член) не являются "пустыми"
        if (self.__a is None) or (self.__b is None):
            raise LogRegError('Parameters have not been specified!')
        # проверить, что корректно задана входная матрица X
        if (X is None) or ((not isinstance(X, numpy.ndarray)) and (not isinstance(X, scipy.sparse.spmatrix))) or\
                (X.ndim != 2) or (X.shape[1] != self.__b.shape[0]):
            raise LogRegError('Input data are wrong!')
        # вычислить искомый массив вероятностей
        return 1.0 / (1.0 + numpy.exp(-X.dot(self.__b) - self.__a))

    def predict(self, X):
        """ Распознать, к какому из двух классов относятся входные объекты.
        :param X - двумерный numpy.ndarray-массив, описывающий векторы признаков входных объектов
        (одна строка - один вектор признаков, количество строк равно количеству входных объектов,
        количество столбцов равно количеству признаков объекта).
        :return одномерный numpy.ndarray-массив, описывающий результаты распознавания каждого из входных объектов в виде
        1 (объект относится к первому классу) или 0 (объект относится ко второму классу). Число элементов этого массива
        равно количеству строк матрицы X, т.е. количеству входных объектов.
        """
        return (self.transform(X) >= self.__th).astype(numpy.float)

    def fit(self, X, y, eps=0.001, lr_max=1.0, max_iters = 1000):
        """ Обучить логистическую регрессию на заданном обучающем множестве градиентным методом.
        :param X - двумерный numpy.ndarray-массив, описывающий векторы признаков входных объектов обучающего множества
        (одна строка - один вектор признаков, количество строк равно количеству входных объектов, количество столбцов
        равно количеству признаков объекта).
        :param y - одномерный numpy.ndarray-массив, описывающий желаемые результаты распознавания каждого из входных
        объектов обучающего множества в виде 1 (объект относится к первому классу) или 0 (объект относится ко второму
        классу). Число элементов этого массива равно количеству строк матрицы X, т.е. количеству входных объектов.
        :param eps - чувствительность алгоритма к изменению целевой функции (в нашем случае - логарифма функции
        правдоподобия) после очередного шага алгоритма. Если новое значение целевой функции не превышает старое значение
        более чем на eps либо же вообще меньше старого значения, то обучение прекращается.
        :param lr_max - максимальная длина коэффициента скорости обучения (этот коэффициент будет адаптивным, т.е.
        автоматически подбираться на каждом шаге в направлении градиента, и допустимый диапазон изменений - это
        [0; lr_max]).
        :param max_iters - максимальное число шагов (итераций) алгоритма обучения. Если алгоритм обучения выполнил
        max_iters шагов, но изменения целевой функции по-прежнему велики, т.е. критерий останова не выполнен, то
        обучение всё равно прекращается.
        """
        # проверяем, правильно ли задано обучающее множество (если нет, то генерируем исключение)
        if (X is None) or (y is None) or ((not isinstance(X, numpy.ndarray)) and
                                              (not isinstance(X, scipy.sparse.spmatrix))) or\
                (X.ndim != 2) or (not isinstance(y, numpy.ndarray)) or (y.ndim != 1) or (X.shape[0] != y.shape[0]):
            raise LogRegError('Train data are wrong!')
        # проверяем, правильно ли заданы параметры алгоритма обучения (если нет, то генерируем исключение)
        if (eps <= 0.0) or (lr_max <= 0.0) or (max_iters < 1):
            raise LogRegError('Train parameters are wrong!')
        # инициализируем свободный член и коэффициенты регрессии случайными значениями
        # случайные значения берутся из равномерного распределения [-0.5;0.5]
        self.__a = numpy.random.rand(1)[0] - 0.5
        self.__b = numpy.random.rand(X.shape[1]) - 0.5
        # вычисляем логарифм функции правдоподобия в начальной точке, т.е. сразу после инициализации
        f_old = self.__calculate_log_likelihood(X, y, self.__a, self.__b)
        print('{0:>5}\t{1:>17.12f}'.format(0, f_old))
        stop = False  # флажок, определяющий, выполнен ли критерий останова (сначала он не выполнен, разумеется)
        iterations_number = 1  # счётчик числа шагов (итераций) алгоритма
        while not stop:  # пока не выполнен критерий останова, продолжаем обучение
            gradient = self.__calculate_gradient(X, y)  # вычисляем градиент в текущей точке
            lr = self.__find_best_lr(X, y, gradient, lr_max)  # вычисляем оптимальный шаг в направлении градиента
            self.__a = self.__a + lr * gradient[0]  # корректируем свободный член логистической регрессии
            self.__b = self.__b + lr * gradient[1]  # корректируем коэффициенты логистической регрессии
            # логарифм функции правдоподобия в новой точке (с новым свободным членом и новыми коэффициентами регрессии)
            f_new = self.__calculate_log_likelihood(X, y, self.__a, self.__b)
            print('{0:>5}\t{1:>17.12f}'.format(iterations_number, f_new))
            # если логарифм функции правдоподобия увеличился чуть-чуть или даже уменьшился, то всё, хватит обучаться
            if (f_new - f_old) < eps:
                stop = True
            # если логарифм функции правдоподобия увеличился существенно, то проверяем число шагов алгоритма
            else:
                f_old = f_new
                iterations_number += 1  # увеличиваем счётчик числа шагов
                if iterations_number >= max_iters:  # если число шагов алгоритма слишком велико, то всё
                    stop = True
        # выводим на экран причину, по которой завершился алгоритм обучения
        if iterations_number < max_iters:
            print('The algorithm is stopped owing to very small changes of log-likelihood function.')
        else:
            print('The algorithm is stopped after the maximum number of iterations.')
        self.__th = self.__calc_best_th(y, self.transform(X))

    def __calculate_log_likelihood(self, X, y, a, b):
        """ Вычислить логарифм функции правдоподобия на заданном обучающем множестве для заданных параметров регрессии
        (т.е. здесь в качестве параметров регрессии - свободного члена и коэффициентов - используются соответствующие
        аргументы метода, а не атрибуты класса self.__a и self.__b).
        :param X - двумерный numpy.ndarray-массив, описывающий векторы признаков входных объектов обучающего множества
        (одна строка - один вектор признаков, количество строк равно количеству входных объектов, количество столбцов
        равно количеству признаков объекта).
        :param y - одномерный numpy.ndarray-массив, описывающий желаемые результаты распознавания каждого из входных
        объектов обучающего множества в виде 1 (объект относится к первому классу) или 0 (объект относится ко второму
        классу). Число элементов этого массива равно количеству строк матрицы X, т.е. количеству входных объектов.
        :param a - свободный член логистической регрессии.
        :param b - одномерный numpy.ndarray-массив коэффициентов логистической регрессии.
        :return Логарифм функции правдоподобия.
        """
        eps = 0.000001  # малое число, предотвращающее появление нуля под логарифмом
        p = 1.0 / (1.0 + numpy.exp(-X.dot(b) - a))
        return numpy.sum(y * numpy.log(p + eps) + (1.0 - y) * numpy.log(1.0 - p + eps))

    def __calculate_gradient(self, X, y):
        """ Вычислить градиент от логарифма функции правдоподобия на заданном обучающем множестве.
        :param X - двумерный numpy.ndarray-массив, описывающий векторы признаков входных объектов обучающего множества
        (одна строка - один вектор признаков, количество строк равно количеству входных объектов, количество столбцов
        равно количеству признаков объекта).
        :param y - одномерный numpy.ndarray-массив, описывающий желаемые результаты распознавания каждого из входных
        объектов обучающего множества в виде 1 (объект относится к первому классу) или 0 (объект относится ко второму
        классу). Число элементов этого массива равно количеству строк матрицы X, т.е. количеству входных объектов.
        :return Градиент от логарифма функции правдоподобия, представленный в виде двухэлементного кортежа, первым
        элементом которого является частная производная по свободному члену регрессии (вещественное число), а вторым
        элементом - вектор частных производных по соответствующим коэффициентам регрессии (одномерный
        numpy.ndarray-массив вещественных чисел).
        """
        p = 1.0 / (1.0 + numpy.exp(-X.dot(self.__b) - self.__a))
        da = numpy.sum(y - p)
        db = X.transpose().dot(y - p)
        return (da, db)

    def __find_best_lr(self, X, y, gradient, lr_max):
        """ По методу золотого сечения найти оптимальный шаг изменения параметров регрессии в направлении градиента
        (т.е. оптимальный коэффициент скорости обучения).
        :param X - двумерный numpy.ndarray-массив, описывающий векторы признаков входных объектов обучающего множества
        (одна строка - один вектор признаков, количество строк равно количеству входных объектов, количество столбцов
        равно количеству признаков объекта).
        :param y - одномерный numpy.ndarray-массив, описывающий желаемые результаты распознавания каждого из входных
        объектов обучающего множества в виде 1 (объект относится к первому классу) или 0 (объект относится ко второму
        классу). Число элементов этого массива равно количеству строк матрицы X, т.е. количеству входных объектов.
        :param gradient - градиент от логарифма функции правдоподобия, представленный в виде двухэлементного кортежа,
        первым элементом которого является частная производная по свободному члену регрессии (вещественное число), а
        вторым элементом - вектор частных производных по соответствующим коэффициентам регрессии (одномерный
        numpy.ndarray-массив вещественных чисел).
        :param lr_max - максимально допустимый коэффициент скорости обучения, т.е. верхняя граница диапазона поиска
        оптимальной величины этого коэффициента (нижняя граница всегда равна нулю).
        :return Оптимальная величина коэффициента скорости обучения (вещественное число).
        """
        lr_min = 0.0
        theta = (1.0 + math.sqrt(5.0)) / 2.0
        eps = 0.00001 * (lr_max - lr_min)
        lr1 = lr_max - (lr_max - lr_min) / theta
        lr2 = lr_min + (lr_max - lr_min) / theta
        while abs(lr_min - lr_max) >= eps:
            y1 = self.__calculate_log_likelihood(X, y, self.__a + lr1 * gradient[0], self.__b + lr1 * gradient[1])
            y2 = self.__calculate_log_likelihood(X, y, self.__a + lr2 * gradient[0], self.__b + lr2 * gradient[1])
            if y1 <= y2:
                lr_min = lr1
                lr1 = lr2
                lr2 = lr_min + (lr_max - lr_min) / theta
            else:
                lr_max = lr2
                lr2 = lr1
                lr1 = lr_max - (lr_max - lr_min) / theta
        return (lr_max - lr_min) / 2.0

    def __calc_quality(self, y_target, y_real):
        n = y_target.shape[0]
        quality = {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0}
        for ind in range(n):
            if y_target[ind] > 0.0:
                if y_real[ind] > 0.0:
                    quality['tp'] += 1
                else:
                    quality['fn'] += 1
            else:
                if y_real[ind] > 0.0:
                    quality['fp'] += 1
                else:
                    quality['tn'] += 1
        return quality

    def __calc_best_th(self, y_target, y_real):
        best_th = 0.0
        min_dist = 1.0
        for th in map(lambda a: float(a) / 100.0, range(101)):
            quality = self.__calc_quality(y_target, (y_real >= th).astype(numpy.float))
            tpr = float(quality['tp']) / float(quality['tp'] + quality['fn'])
            fpr = float(quality['fp']) / float(quality['tn'] + quality['fp'])
            dist = math.sqrt((0.0 - fpr) * (0.0 - fpr) + (1.0 - tpr) * (1.0 - tpr))
            if dist < min_dist:
                min_dist = dist
                best_th = th
        return best_th

def load_mnist_for_demo(sparse=False):
    """ Загрузить данные корпуса MNIST, чтобы продемонстрировать применение логистической регрессии для распознавания
    рукописных цифр от 0 до 9 (всего десять классов, 60 тыс. обучающих картинок и 10 тыс. тестовых картинок).
    :param sparse - флаг, показывающий, представлять ли множество векторов признаков в виде разреженной матрицы
    scipy.sparse.csr_matrix или же в виде обычной матрицы numpy.ndarray.
    :return Кортеж из двух элементов: обучающего и тестового множества. Каждое из множеств - как обучающее, так и
    тестовое - тоже задаётся в виде двухэлементого кортежа, первым элементом которого является множество векторов
    признаков входных объектов (двумерный numpy.ndarray-массив, число строк в котором равно числу входных объектов, а
    число столбцов равно количеству признаков объекта), а вторым элементом - множество желаемых выходных сигналов для
    каждого из соответствующих входных объектов (одномерный numpt.ndarray-массив, число элементов в котором равно числу
    входных объектов).
    """
    from sklearn.datasets import fetch_mldata  # импортируем специальный модуль из библиотеки ScikitLearn
    # загружаем MNIST из текущей директории или Интернета, если в текущей директории этих данных нет
    mnist = fetch_mldata('MNIST original', data_home='.')
    # получаем и нормируем вектора признаков для первых 60 тыс. картинок из MNIST, используемых для обучения
    # (матрица яркостей пикселей 28x28 -> одномерный вектор 784 признаков)
    if sparse:
        X_train = scipy.sparse.csr_matrix(mnist.data[0:60000].astype(numpy.float) / 255.0)
    else:
        X_train = mnist.data[0:60000].astype(numpy.float) / 255.0
    y_train = mnist.target[0:60000]  # получаем желаемые выходы (цифры от 0 до 9) для 60 тыс. обучающих картинок
    # получаем и нормируем вектора признаков для следующих 10 тыс. картинок из MNIST, используемых для тестирования
    # (матрица яркостей пикселей 28x28 -> одномерный вектор 784 признаков)
    if sparse:
        X_test = scipy.sparse.csr_matrix(mnist.data[60000:].astype(numpy.float) / 255.0)
    else:
        X_test = mnist.data[60000:].astype(numpy.float) / 255.0
    y_test = mnist.target[60000:]  # получаем желаемые выходы (цифры от 0 до 9) для 10 тыс. тестовых картинок
    return ((X_train, y_train), (X_test, y_test))


if __name__ == '__main__':
    # если мы используем этот модуль как главный, а не просто как Python-библиотеку, то запускаем демо-пример на MNIST
    import os.path  # импортируем стандартный модуль для работы с файлами
    train_set, test_set = load_mnist_for_demo(True)  # загружаем обучающие и тестовые данные MNIST
    # для 10-классовой классификации создаём 10 бинарных (2-классовых) классификаторов на основе логистической регрессии
    classifiers = list()
    for recognized_class in range(10):
        classifier_name = 'log_reg_for_MNIST_{0}.txt'.format(recognized_class)
        new_classifier = LogisticRegression()
        if os.path.exists(classifier_name):
            new_classifier.load(classifier_name)
        else:
            new_classifier.fit(train_set[0], (train_set[1] == recognized_class).astype(numpy.float))
            new_classifier.save(classifier_name)
        classifiers.append(new_classifier)
    # на тестовом множестве вычисляем результаты распознавания цифр коллективом из 10 обученных логистических регрессий
    # (принцип принятия решений таким коллективом: входной вектор признаков считается отнесённым к тому классу, чья
    # логистическая регрессия выдала наибольшую вероятность).
    n_test_samples = test_set[0].shape[0]
    outputs = numpy.empty((n_test_samples, 10), dtype=numpy.float)
    for recognized_class in range(10):
        outputs[:, recognized_class] = classifiers[recognized_class].transform(test_set[0])
    results = outputs.argmax(1)
    # сравниваем полученные результаты с эталонными и оцениваем процент ошибок коллектива логистических регрессий
    n_errors = numpy.sum(results != test_set[1])
    print('Errors on test set: {0:%}'.format(float(n_errors) / float(n_test_samples)))