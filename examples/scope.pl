# This program demonstrates lexically scoped variables.
# It should print out the numbers 2 and 10 in sequence.

var x;
procedure a;
	var x;
	begin
		x := 2;
		! x
	end;
begin
	x := 10;
	call a;
	! x
end.