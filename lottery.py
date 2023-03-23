import smartpy as sp


class Lottery(sp.Contract):
    def __init__(self, _admin):
        # Storage Block: Storage and variables of the contract definition
        self.init(
            players=sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost=sp.tez(1),
            tickets_available=sp.nat(5),
            tickets_sold=sp.nat(0),
            max_tickets=sp.nat(5),
            admin=_admin,
        )

    @sp.entry_point
    def buy_ticket(self, quantity):
        sp.set_type(quantity, sp.TNat)

        # Sanity checks
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")
        sp.verify(self.data.max_tickets >= quantity, "INVALID AMOUNT")
        sp.verify(sp.amount >= sp.mul(
            quantity, self.data.ticket_cost), "INSUFFICIENT FUNDS")

        player_length = sp.len(self.data.players)

        sp.for i in sp.range(0, quantity):
            self.data.players[player_length] = sp.sender

        self.data.tickets_available = sp.as_nat(
            self.data.tickets_available - quantity)

        self.data.tickets_sold += quantity

        # Return extra tez balance to the sender
        total_cost = sp.mul(quantity, self.data.ticket_cost)
        extra_balance = sp.amount - total_cost
        sp.if extra_balance > sp.mutez(0):
            sp.send(sp.sender, extra_balance)

    @sp.entry_point
    def change_ticket_cost(self, new_cost):
        sp.set_type(new_cost, sp.TMutez)

        # Sanity Checks
        sp.verify(self.data.tickets_sold == 0,
                  "CANNOT CHANGE TICKET VALUE MIDGAME")

        # Change Ticket Cost
        self.data.ticket_cost = new_cost

    @sp.entry_point
    def change_max_ticket(self, new_max):
        sp.set_type(new_max, sp.TNat)

        # Sanity Checks
        sp.verify(self.data.tickets_sold == 0,
                  "CANNOT CHANGE MAXIMUM TICKET VALUE MIDGAME")

        # Change Ticket Cost
        self.data.max_tickets = new_max

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        # Sanity checks
        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 0, "GAME IS YET TO END")

        # Pick a winner
        winner_id = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_id]

        # Send the reward to the winner
        sp.send(winner_address, sp.balance)

        # Reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def default(self):
        sp.failwith("NOT ALLOWED")


@sp.add_test(name="main")
def test():
    scenario = sp.test_scenario()

    # Test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")

    # Contract instance
    lottery = Lottery(admin.address)
    scenario += lottery

    # change_ticket_cost
    scenario.h2("change_ticket (valid test)")
    scenario += lottery.change_ticket_cost(sp.tez(2)).run()
    scenario += lottery.change_ticket_cost(sp.tez(3)).run()

    # change_max_ticket
    scenario.h2("change_max_ticket (valid test)")
    scenario += lottery.change_max_ticket(10).run()
    scenario += lottery.change_max_ticket(3).run()

    # buy_ticket
    scenario.h2("buy_ticket (valid test)")
    scenario += lottery.buy_ticket(3).run(amount=sp.tez(10), sender=alice)
    scenario += lottery.buy_ticket(2).run(amount=sp.tez(6), sender=bob)

    # buy_ticket (failure check)
    scenario.h2("change_ticket (valid test)")
    scenario += lottery.change_ticket_cost(sp.tez(2)).run(valid=False)
    scenario += lottery.change_ticket_cost(sp.tez(3)).run(valid=False)

    scenario.h2("buy_ticket (failure test)")
    scenario += lottery.buy_ticket(1).run(amount=sp.tez(5),
                                          sender=alice, valid=False)

    # end_game
    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game(21).run(sender=admin)
