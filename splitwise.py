from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


@dataclass(frozen=True)
class Member:
    name: str

@dataclass
class Expense:
    description: str
    amount: float
    payer: Member
    # one of: "equal", "shares", "exact"
    split_mode: str = "equal"
    # For "shares": {Member: share_weight}; For "exact": {Member: amount_owed}
    split_details: Optional[Dict[Member, float]] = None

@dataclass
class Group:
    name: str
    members: List[Member] = field(default_factory=list)
    expenses: List[Expense] = field(default_factory=list)

    def add_member(self, name: str) -> Member:
        m = Member(name)
        self.members.append(m)
        return m

    def add_expense(self, description: str, amount: float, payer: Member,
                    split_mode: str = "equal",
                    split_details: Optional[Dict[Member, float]] = None) -> Expense:
        # basic validation
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        if payer not in self.members:
            raise ValueError("Payer must be a member of the group.")
        if split_mode not in {"equal", "shares", "exact"}:
            raise ValueError("split_mode must be 'equal', 'shares', or 'exact'.")
        if split_mode != "equal":
            if not split_details or any(m not in self.members for m in split_details):
                raise ValueError("All split_details members must belong to the group.")
        exp = Expense(description, amount, payer, split_mode, split_details)
        self.expenses.append(exp)
        return exp

    # ---------- Ledger + settlements ----------

    def balances(self) -> Dict[Member, float]:
        """
        Positive balance => others owe this member
        Negative balance => this member owes others
        """
        bal = defaultdict(float)

        for e in self.expenses:
            # Credit the payer for the full amount
            bal[e.payer] += e.amount

            # Compute how much each member owes for this expense
            if e.split_mode == "equal":
                participants = self.members
                share = round(e.amount / len(participants), 2)
                # Adjust final cent rounding on the last person to keep totals exact
                running = 0.0
                for i, m in enumerate(participants):
                    owed = share
                    running += owed
                    if i == len(participants) - 1:
                        owed += round(e.amount - running, 2)  # fix rounding drift
                    bal[m] -= owed

            elif e.split_mode == "shares":
                total_shares = sum(e.split_details.values())
                running = 0.0
                items = list(e.split_details.items())
                for i, (m, w) in enumerate(items):
                    owed = round(e.amount * (w / total_shares), 2)
                    running += owed
                    if i == len(items) - 1:
                        owed += round(e.amount - running, 2)
                    bal[m] -= owed

            elif e.split_mode == "exact":
                # Validate totals match
                total_exact = round(sum(e.split_details.values()), 2)
                if total_exact != round(e.amount, 2):
                    raise ValueError(f"Exact splits ({total_exact}) must sum to expense amount ({e.amount}).")
                for m, owed in e.split_details.items():
                    bal[m] -= round(owed, 2)

        # Tiny epsilon cleanup
        for m in bal:
            if abs(bal[m]) < 0.005:
                bal[m] = 0.0

        return dict(bal)

    def settlements(self) -> List[Tuple[Member, Member, float]]:
        """
        Greedy min-cash-flow: returns list of (debtor -> creditor, amount).
        """
        bal = self.balances()
        debtors = []
        creditors = []

        for m, b in bal.items():
            if b < 0:
                debtors.append([m, -b])     # owes
            elif b > 0:
                creditors.append([m, b])    # is owed

        # Sort for deterministic output (optional)
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)

        res = []
        i = j = 0
        while i < len(debtors) and j < len(creditors):
            dm, d_amt = debtors[i]
            cm, c_amt = creditors[j]
            pay = round(min(d_amt, c_amt), 2)
            if pay > 0:
                res.append((dm, cm, pay))
            debtors[i][1] = round(d_amt - pay, 2)
            creditors[j][1] = round(c_amt - pay, 2)
            if debtors[i][1] == 0:
                i += 1
            if creditors[j][1] == 0:
                j += 1

        return res


if __name__ == "__main__":
    g = Group("Ski Trip")
    alice = g.add_member("Alice")
    bob   = g.add_member("Bob")
    chris = g.add_member("Chris")

    # Alice paid €120 for groceries, split equally among all -- KEEP THIS ONLY -- KEEP EQUAL?
    g.add_expense("Groceries", 120.00, payer=alice, split_mode="equal")

    # # Bob paid €60 for gas, split by shares: Alice 1, Bob 2, Chris 1
    # g.add_expense(
    #     "Gas", 60.00, payer=bob, split_mode="shares",
    #     split_details={alice: 1, bob: 2, chris: 1}
    # )

    # # Chris paid lift tickets with exact amounts (e.g., someone used a discount)
    # g.add_expense(
    #     "Lift tickets", 150.00, payer=chris, split_mode="exact",
    #     split_details={alice: 40.00, bob: 60.00, chris: 50.00}
    # )

    print("Balances (+: is owed, -: owes):")
    for m, b in g.balances().items():
        print(f"  {m.name:>5}: {b:.2f}")

    print("\nSuggested settlements:")
    for debtor, creditor, amt in g.settlements():
        print(f"  {debtor.name} -> {creditor.name}: €{amt:.2f}")
