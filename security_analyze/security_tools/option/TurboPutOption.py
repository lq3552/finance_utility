import numpy as np

class TurboPutOption(object):

    def __init__(self, code: str, barrier: np.float64, basiswert: np.float64, 
                 bezugsverhaeltnis: int = 10):
        '''
        Input:
	        code: Name oder Code der Aktie
            barrier: die Knock-out-Barrier, fuer Turbo ist sie gleich dem Strike
            basiswert: der aktuelle Kurs der Aktie
            bezugsverhaeltnis: das Verhaeltnis vom potenziellen Gewinn beim Leerverkauf einer Aktie 
                              zum Wert eines Put-Optionscheins, normalerweise ist es gleich 10
        '''
        self._code = code
        self._barrier = barrier
        self._basiswert = basiswert
        self._bezugsverhaeltnis = bezugsverhaeltnis
        self._optionskurs = barrier - basiswert
        self._hebel = basiswert / self._optionskurs # Hebel ist dynamisch nach dem Aktienkurs
        self._optionskurs /= self._bezugsverhaeltnis

    def info(self):
        return (self._code + '_' + str(self._barrier), round(self._optionskurs, 2), round(self._hebel, 2))

    def warnen_vorm_rueckgang(self, schwelle: list = [5., 10.]) -> list:
        '''
        Warnung vorm deutlichen Rueckgang des Optionkurs
            input:
                schewelle: eine Liste der Prozente, um die sich der Basiswert steigert
            output:
                warnung: eine List der Prozente, um die sich der Optionkurs senkt
        '''
        warnung = []
        for p in schwelle:
            warnung.append(round(self._hebel * p, 2))
        return warnung


