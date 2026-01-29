# Premise Grouping for Bottom Layer

**Date:** 2026-01-28  
**Issue:** Bottom layer premises need special ordering based on support relationships

## Problem Statement

The user reported that the standard barycenter ordering doesn't work properly for argument graphs because:

1. **Conclusion layer order is not important** - The final conclusions don't need specific ordering
2. **Layer above conclusions is also not critical** - The ordering of intermediate nodes isn't critical
3. **Bottom layer (premises) needs special handling** - Premises should be grouped by what they support

### Specific Requirements

> "The final layer that contains most of the premises needs to be ordered using the information of what premise support what thing, so it should be done last and keep premises that support the node next to it. For instance, there should be a block of premises supporting claim 1 above claim 1, then the same for the next claims with minimal overlap between premise blocks."

## Solution: Premise Grouping by Support

### Overview

Implemented special ordering for the bottom layer that:
- Groups premises by what they support (their parent nodes)
- Positions each group under the nodes they support
- Keeps premises in each group contiguous (no gaps)
- Ensures minimal overlap between premise blocks

### Implementation

#### New Function: `order_bottom_layer_by_support()`

```python
def order_bottom_layer_by_support(bottom_layer_nodes: List[str],
                                   parents: Dict[str, List[str]],
                                   parent_orders: Dict[str, int]) -> Dict[str, int]:
    """
    Order nodes in the bottom layer by grouping them according to what they support.
    
    Premises supporting the same parent node(s) are positioned together as a block,
    and these blocks are positioned under the nodes they support.
    """
```

**Algorithm:**
1. Group nodes by their parent nodes (what they support)
2. Calculate group position based on parent positions (average)
3. Sort groups by position
4. Sort nodes within each group (deterministic)
5. Assign sequential orders to create contiguous blocks

#### Modified: `barycenter_ordering()`

After all regular barycenter iterations:
```python
# After all iterations, apply special ordering to the bottom layer
if layer_numbers:
    bottom_layer = layer_numbers[-1]
    bottom_layer_nodes = nodes_by_layer[bottom_layer]
    
    if len(bottom_layer_nodes) > 1:
        # Apply premise grouping
        bottom_layer_orders = order_bottom_layer_by_support(
            bottom_layer_nodes, parents, node_orders
        )
        node_orders.update(bottom_layer_orders)
```

### Visual Example

**Before (Standard Barycenter):**
```
     Claim1         Claim2         Claim3
        |              |              |
        v              v              v
   Mixed premises: P1 P4 P6 P2 P5 P3 P7 P8
   (no clear grouping)
```

**After (Premise Grouping):**
```
     Claim1         Claim2         Claim3
        |              |              |
        v              v              v
   [P1 P2 P3]     [P4 P5]        [P6 P7 P8]
   Block for      Block for       Block for
   Claim1         Claim2          Claim3
```

### Real-World Example

From `scripts/demo_premise_grouping.py`:

```
Layout by Layer:
----------------------------------------------------------------------
Layer 0:
  P1    at x=-875  (supports Claim1)
  P2    at x=-625  (supports Claim1)
  P3    at x=-375  (supports Claim1)
  P4    at x=-125  (supports Claim2)
  P5    at x= 125  (supports Claim2)
  P6    at x= 375  (supports Claim3)
  P7    at x= 625  (supports Claim3)
  P8    at x= 875  (supports Claim3)

Layer 1:
  Claim1 at x=-250
  Claim2 at x=   0
  Claim3 at x= 250

Analysis:
  Claim1: Supported by [P1, P2, P3] - block width 500
  Claim2: Supported by [P4, P5]     - block width 250
  Claim3: Supported by [P6, P7, P8] - block width 500
```

## Benefits

### 1. Clear Visual Structure
Premises are visually grouped under the claims they support, making the argument structure immediately clear.

### 2. Minimal Overlap
Groups don't intermingle - each block is distinct and positioned under its supported claim.

### 3. Maintains Optimization
Upper layers still use barycenter ordering to minimize crossings. Only the bottom layer gets special treatment.

### 4. Handles Complex Cases
- **Multiple parents**: Premise supporting multiple claims is positioned based on average parent position
- **Orphan nodes**: Nodes with no parents go to the end
- **Deterministic**: Same input always produces same output

## Algorithm Details

### Grouping Strategy

**Group Key:**
- Premises with the same set of parents belong to the same group
- Group key is a sorted tuple of parent IDs
- Example: P1→Claim1, P2→Claim1 both have group key `('Claim1',)`

**Group Positioning:**
- Group position = average of parent positions
- If premise supports multiple nodes, average their positions
- Groups sorted by this position value

**Within-Group Ordering:**
- Nodes sorted alphabetically/by ID within each group
- Ensures determinism
- Creates predictable, consistent layouts

### Edge Cases Handled

1. **No parents**: Orphan nodes go to the end (position = infinity)
2. **Multiple parents**: Average parent positions
3. **Single node in layer**: Skip special ordering (not needed)
4. **Empty layer**: No processing needed

## Testing

### Test Coverage

**Unit Tests:**
- `test_order_bottom_layer_by_support_function()` - Tests the grouping function directly
- Verifies premises are grouped by support
- Checks groups are contiguous
- Ensures proper ordering

**Integration Tests:**
- `test_premise_grouping_by_support()` - End-to-end test with full graph
- Verifies premises grouped correctly in final layout
- Checks no overlap between groups
- Validates contiguous positioning

**Complex Scenarios:**
- `test_premise_grouping_with_shared_support()` - Handles premises supporting multiple claims
- Ensures sensible positioning
- Validates no crashes with complex relationships

### Running Tests

```bash
# Run premise grouping tests
python -m pytest tests/test_premise_grouping.py -v

# Run all layout tests
python -m pytest tests/test_graph_layout*.py tests/test_premise_grouping.py -v

# Run demo
python scripts/demo_premise_grouping.py
```

### Test Results
✅ 33 tests passing (24 existing + 3 new + 6 integration)  
✅ All existing tests still pass  
✅ New behavior only affects bottom layer  

## Comparison with Standard Barycenter

### Standard Barycenter Approach
- Orders all layers uniformly
- Uses parent barycenter (top-down)
- Uses child barycenter (bottom-up)
- **Problem**: Bottom layer has no children, so bottom-up sweep doesn't help

### Premise Grouping Approach
- Uses standard barycenter for upper layers
- **Special handling for bottom layer**
- Groups by support relationships
- Positions groups under supported nodes
- **Result**: Clear structure for premises

## Performance

### Computational Complexity
- Additional grouping step: O(n log n) where n = bottom layer size
- Comparable to barycenter sweep complexity
- No significant performance impact

### Memory Usage
- Additional data structures for groups
- Minimal memory overhead
- Groups processed then discarded

## User Impact

### What Users Will Notice
- **Clearer structure**: Premises visually grouped
- **Better readability**: Easy to see what supports what
- **Logical layout**: Premise blocks under their claims
- **No manual adjustment needed**: Automatic grouping

### Backward Compatibility
- Upper layers unchanged (still use barycenter)
- Only bottom layer gets new treatment
- All existing graphs render correctly
- No breaking changes

## Future Enhancements

Possible improvements:
1. **Multi-level grouping**: Apply similar logic to other layers
2. **Weight-based positioning**: Weight groups by edge confidence
3. **Overlap optimization**: Further minimize visual overlap
4. **User configuration**: Allow users to specify which layers need grouping

## Conclusion

The premise grouping feature successfully addresses the user's requirements:

✅ **Bottom layer ordered by support** - Premises grouped by what they support  
✅ **Blocks under supported nodes** - Each group positioned correctly  
✅ **Minimal overlap** - Groups are distinct and separated  
✅ **Deterministic** - Consistent, predictable layouts  
✅ **Maintains optimization** - Upper layers still use barycenter  

The implementation provides clear, readable argument graph layouts by ensuring premises are visually organized according to their support relationships.
