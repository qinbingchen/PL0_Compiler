# This program calculates the first K values of the fibonacci sequence.

CONST K = 20;

VAR m, n, k, count;

BEGIN
	m := 1;
	n := 1;
	k := 1;
	count := 0;

	WHILE count <= K DO
	BEGIN
		WRITE(k);

		k := n;
		n := m + n;
		m := k;

		count := count + 1
	END
END.
