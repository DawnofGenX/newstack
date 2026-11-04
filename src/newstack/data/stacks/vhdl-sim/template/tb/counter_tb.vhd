-- A self-checking testbench: every check is an assert, so `ghdl -r` with
-- --assert-level=error fails the run as soon as the design is wrong.
--
-- The inject_fault generic exists so the shipped workflow can prove the
-- assertions have teeth: run it with -ginject_fault=true and the run MUST fail.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;

entity counter_tb is
  generic (
    inject_fault : boolean := false
  );
end entity counter_tb;

architecture sim of counter_tb is

  constant width : positive := 8;
  constant period : time := 10 ns;

  signal clk   : std_logic := '0';
  signal rst   : std_logic := '1';
  signal en    : std_logic := '0';
  signal up    : std_logic := '1';
  signal load  : std_logic := '0';
  signal d_in  : std_logic_vector(width - 1 downto 0) := (others => '0');
  signal q     : std_logic_vector(width - 1 downto 0);
  signal carry : std_logic;

  signal running : boolean := true;

  procedure check(
    constant actual   : in integer;
    constant expected : in integer;
    constant message  : in string
  ) is
  begin
    assert actual = expected
      report message & ": got " & integer'image(actual) & ", want " & integer'image(expected)
      severity error;
  end procedure;

begin

  clk <= (not clk) after period / 2 when running else '0';

  dut : entity work.counter
    generic map (width => width)
    port map (
      clk   => clk,
      rst   => rst,
      en    => en,
      up    => up,
      load  => load,
      d_in  => d_in,
      q     => q,
      carry => carry
    );

  stimulus : process
    variable expected : integer;
  begin
    -- reset clears the counter
    wait until rising_edge(clk);
    rst <= '0';
    wait until rising_edge(clk);
    wait for 1 ns;
    check(to_integer(unsigned(q)), 0, "reset value");

    -- count up three times
    en <= '1';
    for i in 1 to 3 loop
      wait until rising_edge(clk);
    end loop;
    wait for 1 ns;
    check(to_integer(unsigned(q)), 3, "three counts up");

    -- hold: enable low keeps the value
    en <= '0';
    wait until rising_edge(clk);
    wait until rising_edge(clk);
    wait for 1 ns;
    check(to_integer(unsigned(q)), 3, "disabled counter holds");

    -- count down
    up <= '0';
    en <= '1';
    wait until rising_edge(clk);
    wait for 1 ns;
    check(to_integer(unsigned(q)), 2, "one count down");

    -- synchronous load wins over counting
    load <= '1';
    d_in <= std_logic_vector(to_unsigned(200, width));
    wait until rising_edge(clk);
    load <= '0';
    wait for 1 ns;
    check(to_integer(unsigned(q)), 200, "load");

    -- wrap and carry (counting up again from 200)
    up <= '1';
    for i in 1 to 55 loop
      wait until rising_edge(clk);
    end loop;
    wait for 1 ns;
    check(to_integer(unsigned(q)), 255, "counts up to all ones");
    wait for 1 ns;
    assert carry = '1' report "carry should be high at all ones" severity error;
    wait until rising_edge(clk);
    wait for 1 ns;
    check(to_integer(unsigned(q)), 0, "wraps to zero");
    wait for 1 ns;
    assert carry = '0' report "carry should be low after wrapping" severity error;

    -- the fault injection the workflow relies on
    if inject_fault then
      wait for 1 ns;
    check(to_integer(unsigned(q)), 42, "deliberate fault");
    end if;

    report "PASS: counter testbench complete" severity note;
    running <= false;
    wait for period;
    finish;
  end process;

end architecture sim;
