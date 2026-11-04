-- An 8-bit up/down counter with a synchronous load and a carry output.
-- Written to be read: one process, no latches, every branch inside the clock.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity counter is
  generic (
    width : positive := 8
  );
  port (
    clk    : in  std_logic;
    rst    : in  std_logic;
    en     : in  std_logic;
    up     : in  std_logic;
    load   : in  std_logic;
    d_in   : in  std_logic_vector(width - 1 downto 0);
    q      : out std_logic_vector(width - 1 downto 0);
    carry  : out std_logic
  );
end entity counter;

architecture rtl of counter is
  signal value : unsigned(width - 1 downto 0) := (others => '0');
begin

  process (clk)
  begin
    if rising_edge(clk) then
      if rst = '1' then
        value <= (others => '0');
      elsif load = '1' then
        value <= unsigned(d_in);
      elsif en = '1' then
        if up = '1' then
          value <= value + 1;
        else
          value <= value - 1;
        end if;
      end if;
    end if;
  end process;

  q <= std_logic_vector(value);

  -- Carry is a level, not a pulse: it holds while the counter is all ones and
  -- counting up, so a downstream stage can sample it on the same edge.
  carry <= '1' when (up = '1' and value = (value'range => '1')) else '0';

end architecture rtl;
